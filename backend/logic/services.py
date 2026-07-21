""" Main app business logic """

import os
import re

import time
import json

import numpy as np

import fitz
import chromadb

from sentence_transformers import SentenceTransformer
from groq import Groq, RateLimitError, APIStatusError

from llama_cpp import Llama

import core.settings as settings

class LawRetriever:
    def __init__(self):
        print(" > [LawRetriever] Init started.")
        try:
            self.embedder = SentenceTransformer(settings.SEN_TRANSFORMER_MODEL, device='cpu')
            print(" > [LawRetriever] Embedder loaded.")
        except Exception as e:
            print(f" > [LawRetriever] Failed to load embedder: {e}")
            raise

        try:
            self.db_client = chromadb.PersistentClient(path=settings.LAW_DB_PATH)
            print(" > [LawRetriever] DB client connected.")
        except Exception as e:
            print(f" > [LawRetriever] Failed to connect DB: {e}")
            raise

        try:
            self.collection = self.db_client.get_collection("housing_law")
            print(" > [LawRetriever] Collection loaded.")
        except Exception as e:
            print(f" > [LawRetriever] Collection not found: {e}")
            raise RuntimeError(
                f"Law database not found at {settings.LAW_DB_PATH}. "
                f"Run LawRetriever.build_law_index() before use."
            ) from e

    def find_relevant_articles(self, document_text, top_k=5, max_chars_per_article=800) -> str:
        print(f" > [LawRetriever] Searching top_k={top_k} articles.")
        try:
            query_embedding = self.embedder.encode(
                [document_text[:2000]], normalize_embeddings=True
            ).tolist()
        except Exception as e:
            print(f" > [LawRetriever] Failed to encode query: {e}")
            return "No relevant articles found."

        try:
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k
            )
        except Exception as e:
            print(f" > [LawRetriever] DB query failed: {e}")
            return "No relevant articles found."

        if not results['documents'] or not results['documents'][0]:
            print(" > [LawRetriever] No documents found.")
            return "No relevant articles found."

        print(f" > [LawRetriever] Found {len(results['documents'][0])} articles. Compressing...")

        compressed = []
        for doc in results['documents'][0]:
            try:
                compressed.append(self._compress_document(doc, query_embedding[0], max_chars_per_article))
            except Exception as e:
                print(f" > [LawRetriever] Compression failed for one doc, using raw: {e}")
                compressed.append(doc)

        return "\n\n---\n\n".join(compressed)

    def _compress_document(self, doc_text: str, query_embedding: list, max_chars: int = 800) -> str:
        try:
            header, sep, body = doc_text.partition("\n")
            if not sep:
                header, body = "", doc_text
        except Exception as e:
            print(f" > [LawRetriever] Partition failed: {e}")
            return doc_text

        try:
            sentences = [s for s in re.split(r'(?<=[.!?])\s+', body.strip()) if s]
        except Exception as e:
            print(f" > [LawRetriever] Sentence split failed: {e}")
            return doc_text

        if not sentences or len(doc_text) <= max_chars:
            return doc_text

        try:
            sent_embeddings = self.embedder.encode(sentences, normalize_embeddings=True)
            query_vec = np.array(query_embedding)
            scores = sent_embeddings @ query_vec
        except Exception as e:
            print(f" > [LawRetriever] Scoring failed, returning raw doc: {e}")
            return doc_text

        try:
            ranked_idx = sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True)

            selected = set()
            total_len = len(header)
            for i in ranked_idx:
                if total_len + len(sentences[i]) > max_chars and selected:
                    break
                selected.add(i)
                total_len += len(sentences[i]) + 1

            kept = [sentences[i] for i in sorted(selected)]
            return (header + "\n" if header else "") + " ".join(kept)
        except Exception as e:
            print(f" > [LawRetriever] Ranking failed, returning raw doc: {e}")
            return doc_text

    @staticmethod
    def extract_law_text(pdf_path) -> str:
        print(f" > [LawRetriever] Extracting text from {pdf_path}.")
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            print(f" > [LawRetriever] Failed to open PDF: {e}")
            return ""

        text = ""
        try:
            for page in doc:
                try:
                    text += page.get_text()
                except Exception as e:
                    print(f" > [LawRetriever] Failed to read one page: {e}")
                    continue
        finally:
            try:
                doc.close()
            except Exception as e:
                print(f" > [LawRetriever] Failed to close PDF: {e}")

        print(f" > [LawRetriever] Extracted {len(text)} chars.")
        return text

    @staticmethod
    def split_into_articles(text) -> dict:
        print(" > [LawRetriever] Splitting text into articles.")
        try:
            text = re.sub(r'[ \t]+', ' ', text)
            text = re.sub(r'\n{2,}', '\n', text)
        except Exception as e:
            print(f" > [LawRetriever] Text cleanup failed: {e}")
            return {}

        try:
            pattern = r'Article\s*(\d+(?:-\d+)?)\.\s*([^\n]*)\n(.*?)(?=Article\s*\d+(?:-\d+)?\.|\Z)'
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        except Exception as e:
            print(f" > [LawRetriever] Regex match failed: {e}")
            return {}

        articles = {}
        for num, title, content in matches:
            try:
                clean_content = re.sub(r'\s+', ' ', content.strip())
                if len(clean_content) < 10:
                    continue
                articles[num] = {
                    "title": title.strip(),
                    "content": clean_content
                }
            except Exception as e:
                print(f" > [LawRetriever] Skipped one article ({num}): {e}")
                continue

        print(f" > [LawRetriever] Parsed {len(articles)} articles.")
        return articles

    @staticmethod
    def build_law_index():
        """Rebuilds the ChromaDB collection from scratch — safe to call even
        if the existing collection is missing or corrupted, since it doesn't
        rely on __init__ having succeeded."""
        print(" > [Law index] Build started.")

        raw_text = LawRetriever.extract_law_text(settings.LAW_PDF_PATH)
        if not raw_text:
            print(" > [Law index] No text extracted, aborting.")
            return

        articles = LawRetriever.split_into_articles(raw_text)

        if not articles:
            print(" > [Law index] Parser didn't find any articles.")
            return

        print(f" > [Law index] Found {len(articles)} articles: {list(articles.keys())}")

        try:
            embedder = SentenceTransformer(settings.SEN_TRANSFORMER_MODEL, device='cpu')
        except Exception as e:
            print(f" > [Law index] Failed to load embedder: {e}")
            return

        try:
            client = chromadb.PersistentClient(path=settings.LAW_DB_PATH)
        except Exception as e:
            print(f" > [Law index] Failed to connect DB client: {e}")
            return

        try:
            client.delete_collection("housing_law")
            print(" > [Law index] Old collection deleted.")
        except Exception as e:
            print(f" > [Law index] No old collection to delete (fine): {e}")

        try:
            collection = client.create_collection("housing_law")
        except Exception as e:
            print(f" > [Law index] Failed to create collection: {e}")
            return

        try:
            docs = [f"Article {num}: {v['title']}\n{v['content']}" for num, v in articles.items()]
            embeddings = embedder.encode(docs, normalize_embeddings=True).tolist()
        except Exception as e:
            print(f" > [Law index] Failed to build embeddings: {e}")
            return

        try:
            collection.add(
                documents=docs,
                embeddings=embeddings,
                ids=[f"art_{num}" for num in articles.keys()],
                metadatas=[{"article_num": num, "title": v['title']} for num, v in articles.items()]
            )
            print(f" > [Law index] Done. Saved in {settings.LAW_DB_PATH}.")
        except Exception as e:
            print(f" > [Law index] Failed to write to DB: {e}")

class CensorshipError(Exception):
    """ Error catcher """

class AIService:
    def __init__(self):
        print(" > [AIService] Init started.")
        try:
            api_key = settings.GROQ_KEY
            self.client = Groq(api_key=api_key)
            print(" > [AIService] Groq client ready.")
        except Exception as e:
            print(f" > [AIService] Failed to init Groq client: {e}")
            raise

        self.config_dir = settings.LOGIC_CONF_DIR
        self.active_mode = None

        try:
            self.retriever = LawRetriever()
        except Exception as e:
            print(f" > [AIService] Failed to init LawRetriever: {e}")
            raise

        self._local_llm = None

        # Schema with explanations IN RUSSIAN (For LLM)
        self.finding_schema = {
            "clause_ref": "номер пункта договора, например '3.5' или '5.2'",
            "excerpt": "точная цитата из договора",
            "source": "статья закона, например 'Article 24, para 6' — обязательно, не оставлять пустым",
            "category": "одно из: responsibility | right | obligation | deadline | risk",
            "explanation": "что это значит для нанимателя простыми словами",
            "mitigation": "как переформулировать пункт по закону, или пустая строка если риска нет"
        }
        print(" > [AIService] Init done.")

    def _set_mode(self, mode: str):
        print(f" > [AIService] Setting mode: {mode}.")
        if mode not in settings.GROQ_MODELS:
            print(f" > [AIService] Unknown mode: {mode}.")
            raise ValueError(f"Unknown mode: {mode}.")
        self.active_mode = mode

    def _get_analyzer_system_prompt(self) -> str:
        sys_prompt_path = os.path.join(self.config_dir, f"sys_prompt_{self.active_mode}.txt")
        print(f" > [AIService] Reading analyzer prompt: {sys_prompt_path}.")

        if not os.path.exists(sys_prompt_path):
            print(f" > [AIService] Prompt file missing: {sys_prompt_path}.")
            raise FileNotFoundError(f"{sys_prompt_path} not found.")

        try:
            with open(sys_prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f" > [AIService] Failed to read prompt file: {e}")
            raise

    def _get_censor_system_prompt(self) -> str:
        sys_prompt_path = os.path.join(self.config_dir, "sys_prompt_censor.txt")
        print(f" > [AIService] Reading censor prompt: {sys_prompt_path}.")

        if not os.path.exists(sys_prompt_path):
            print(f" > [AIService] Prompt file missing: {sys_prompt_path}.")
            raise FileNotFoundError(f"{sys_prompt_path} not found.")

        try:
            with open(sys_prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f" > [AIService] Failed to read censor prompt: {e}")
            raise

    def _get_local_llm(self) -> Llama:
        if self._local_llm is None:
            print(f" > [Censor] Loading local LLM: {settings.CENSOR_MODEL}")
            try:
                self._local_llm = Llama(
                    model_path=str(settings.CENSOR_MODEL),
                    n_ctx=4096,
                    verbose=False,
                )
                print(" > [Censor] Local LLM loaded.")
            except Exception as e:
                print(f" > [Censor] Failed to load local LLM: {e}")
                raise
        return self._local_llm

    def censor(self, raw: str) -> str:
        """ Name, adress, company, subscription -> Placeholders """
        print(" > [Censor] Censoring started.")

        try:
            system_prompt = self._get_censor_system_prompt()
        except Exception as e:
            print(f" > [Censor] Failed to get system prompt: {e}")
            raise CensorshipError(f"Censor prompt error: {e}") from e

        try:
            llm = self._get_local_llm()
        except Exception as e:
            print(f" > [Censor] Failed to get local LLM: {e}")
            raise CensorshipError(f"Local LLM error: {e}") from e

        user_message = (
            f"Текст документа:\n---\n{raw}\n---\n\n"
            f"Верни СТРОГО валидный JSON без пояснений.\n"
            f"От твоей работы зависит БЕЗОПАСНОСТЬ всех людей в тексте. Они РЕАЛЬНЫ."
        )

        max_retries = 3
        raw_output = None

        for attempt in range(max_retries):
            print(f" > [Censor] Attempt {attempt}.")
            try:
                completion = llm.create_chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=settings.MODEL_CONTEXT,
                    temperature=0.1,
                    frequency_penalty=0.5,
                    response_format={"type": "json_object"},
                )
                raw_output = completion["choices"][0]["message"]["content"]
                print(f" > [Censor] Found entities:\n{raw_output}")
                break

            except Exception as e:
                print(f" > [Censor] Model error ({attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise CensorshipError(f" > [Censor] Local LLM unavailable: {e}") from e

        try:
            parsed = json.loads(raw_output)
            entities = parsed.get("entities", [])
            print(f" > [Censor] Parsed {len(entities)} entities.")

        except (json.JSONDecodeError, AttributeError) as e:
            print(f" > [Censor] JSON parse failed: {e}")
            raise CensorshipError(f" > [Censor] Invalid JSON: {raw_output!r}") from e

        try:
            return self._apply_censor_replacements(raw, entities)
        except Exception as e:
            print(f" > [Censor] Replacement step crashed, returning original text: {e}")
            return raw

    def _apply_censor_replacements(self, text: str, entities: list) -> str:
        print(" > [Censor] Applying replacements.")
        try:
            flat_occurrences = []

            valid_types = ("ФИО", "АДРЕС", "КОМПАНИЯ")

            for entity in entities:
                try:
                    mask = entity.get("mask")
                    entity_type = entity.get("type")
                    forms = entity.get("forms", [])

                    if not mask or entity_type not in valid_types or not forms:
                        print(f" > [Censor] Skipped invalid entity: {entity!r}")
                        continue

                    for form in forms:
                        if not isinstance(form, str) or not form.strip():
                            continue
                        flat_occurrences.append((form, mask))

                except Exception as e:
                    print(f" > [Censor] Skipped damaged entity {entity!r}: {e}")
                    continue

            print(f" > [Censor] {len(flat_occurrences)} occurrences to replace.")

            # Long phrases first
            flat_occurrences.sort(key=lambda pair: len(pair[0]), reverse=True)

            for occurrence, mask in flat_occurrences:
                try:
                    if occurrence not in text:
                        print(f" > [Censor] Not found: {occurrence!r}")
                        continue
                    text = text.replace(occurrence, mask)
                    print(f" > [Censor] Replaced {occurrence!r} with {mask!r}.")

                except Exception as e:
                    print(f" > [Censor] Failed to replace {occurrence!r}: {e}")
                    continue

            print(f" > [Censor] Censored version: {text}")
            return text

        except Exception as e:
            print(f" > [Censor] Fatal error during censoring, returning original text: {e}")
            return text

    def generate_analysis(self, report, mode: str = 'fast'):
        print(f" > [AI] Generating analysis in mode: {mode}.")

        try:
            self._set_mode(mode)
        except Exception as e:
            print(f" > [AI] Failed to set mode: {e}")
            return None

        try:
            model_name = settings.GROQ_MODELS[mode]
        except Exception as e:
            print(f" > [AI] Model lookup failed: {e}")
            return None

        document_text = report.get("content", "") if isinstance(report, dict) else report
        if not document_text:
            print(" > [AI] Empty document text, aborting.")
            return None

        top_k = 4 if mode == 'fast' else 8

        try:
            law_context = self.retriever.find_relevant_articles(document_text, top_k=top_k)
        except Exception as e:
            print(f" > [AI] Failed to fetch law context: {e}")
            law_context = "No relevant articles found."

        try:
            schema_str = json.dumps(self.finding_schema, ensure_ascii=False)
        except Exception as e:
            print(f" > [AI] Failed to dump schema: {e}")
            return None

        user_message = (
            f"ЗАКОН (exact Article in 'source'):\n{law_context}\n\n"
            f"ДОГОВОР:\n{document_text}\n\n---\n"
            f"Пройди договор пункт за пунктом. Для каждой категории - отдельный объект findings (не объединяй).\n\n"
            f"Правила 'source':\n"
            f"- Точный номер статьи из ЗАКОНА.\n"
            f"- Иначе: 'не найдено в предоставленном законе'.\n"
            f"- Не выдумывай статьи.\n\n"
            f"Правила 'mitigation':\n"
            f"- Для категории 'risk' или для очевидно неадекватных сумм в контексте — ЗАПОЛНИ ОБЯЗАТЕЛЬНО.\n"
            f"- Для остальных категорий - КРАЙНЕ желательно предлагать улучшение.\n\n"
            f"Если не жилищное право - верни {{\"findings\": []}}.\n\n"
            f"Формат:\n{schema_str}\n\n"
            f"Строго JSON: {{\"findings\": [ ... ]}}"
        )

        try:
            system_prompt = self._get_analyzer_system_prompt()
        except Exception as e:
            print(f" > [AI] Failed to load system prompt: {e}")
            return None

        max_retries = 3
        for attempt in range(max_retries):
            print(f" > [AI] Attempt {attempt}.")
            try:
                completion = self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=3000,
                    temperature=0.25,
                    response_format={"type": "json_object"},
                )
                print(" > [AI] Generation succeeded.")
                return completion.choices[0].message.content

            except (RateLimitError, APIStatusError) as e:
                print(f" > [AI] Rate limit hit ({attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait = 15 * (attempt + 1)
                    print(f" > [AI] Waiting {wait}s before retry.")
                    time.sleep(wait)
                    continue
                print(f" > [AI] Critical error (timeout): {e}. Giving up.")
                return None

            except Exception as e:
                print(f" > [AI] Critical error: {e}. Giving up.")
                return None

        print(" > [AI] All retries exhausted.")
        return None

class DocumentProcessor:
    def __init__(self):
        print(" > [DocProcessor] Init started.")
        try:
            self.ai_service = AIService()
        except Exception as e:
            print(f" > [DocProcessor] Failed to init AIService: {e}")
            raise

        #print(" > Building law index...")
        #LawRetriever.build_law_index()

        print("-------------------------------------------------------------------")
        print(" > Analyze started.")

    def _preprocess_file(self, file_text) -> dict:
        print(" > [DocProcessor] Preprocessing file.")
        try:
            preprocessed = self.ai_service.censor(file_text)
            print(" > [DocProcessor] Censoring done.")
            return {"content": preprocessed}
        except Exception as e:
            print(f" > Preprocessing error: {e}")
            return {"content": {}}

    def _main_process(self, user, file_dict) -> dict:
        print(" > [DocProcessor] Main process started.")
        try:
            used_model = "smart" if user["tier"] == "premium" else "fast"
        except Exception as e:
            print(f" > [DocProcessor] Failed to read user tier, using fast: {e}")
            used_model = "fast"

        try:
            return self.ai_service.generate_analysis(file_dict, used_model)
        except Exception as e:
            print(f" > [DocProcessor] Analysis crashed: {e}")
            return None

    def analyze(self, text, user) -> str:
        print(" > [DocProcessor] Analyze called.")
        try:
            raw_dict = self._preprocess_file(text)
        except Exception as e:
            print(f" > [DocProcessor] Preprocess crashed hard: {e}")
            raw_dict = {"content": {}}

        try:
            result = self._main_process(user, raw_dict)
        except Exception as e:
            print(f" > [DocProcessor] Main process crashed hard: {e}")
            result = None

        print(" > [DocProcessor] Analyze finished.")
        print(f" > Final: {result}")
        return result
