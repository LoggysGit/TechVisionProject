""" Main app business logic """

import os
import re

import time
import json

import numpy as np

import fitz
import chromadb
import urllib.request

from sentence_transformers import SentenceTransformer
from groq import Groq, RateLimitError, APIStatusError

from llama_cpp import Llama

import core.settings as settings

class LawRetriever:
    """ Law index builder """

    def __init__(self):
        # Init objects
        self.embedder = SentenceTransformer(settings.SEN_TRANSFORMER_MODEL, device='cpu')
        self.db_client = chromadb.PersistentClient(path=settings.LAW_DB_PATH)

        # Reload collection
        try:
            self.db_client.delete_collection("housing_law")
        except Exception:
            pass
        self.collection = self.db_client.create_collection("housing_law")

        print(" > [LawRetriever] Initted successfully.")

    def _compress_document(self, doc_text: str, query_embedding: list, max_chars: int = 800) -> str:
        """ Compresses document into vectors """

        try:
            # Split document on part
            header, sep, body = doc_text.partition("\n")
            if not sep:
                header, body = "", doc_text

            # Split parts on sentences
            sentences = [s for s in re.split(r'(?<=[.!?])\s+', body.strip()) if s]

            # Validate
            if not sentences or len(doc_text) <= max_chars:
                return doc_text

            # Emded & score
            sent_embeddings = self.embedder.encode(sentences, normalize_embeddings=True)
            query_vec = np.array(query_embedding)
            scores = sent_embeddings @ query_vec

            # Rank articles
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
            print(f" > [LawRetriever] Compressing failed: {e}")
            return doc_text

    def find_relevant_articles(self, document_text: str, top_k: int = 5, max_chars_per_article: int = 800) -> str:
        """ Finds relevan articles by meaning """

        print(f" > [LawRetriever] Searching top_k={top_k} articles.")

        try:
            # Encode query
            query_embedding = self.embedder.encode(
                [document_text[:2000]], normalize_embeddings=True
            ).tolist()

            # Get nearest records
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k
            )

            # Validate
            if not results['documents'] or not results['documents'][0]:
                print(" > [LawRetriever] No documents found.")
                return "No relevant articles found."
            print(f" > [LawRetriever] Found {len(results['documents'][0])} articles. Compressing...")

            # Collect all
            compressed = []
            for doc in results['documents'][0]:
                comp_doc = self._compress_document(doc, query_embedding[0], max_chars_per_article)
                compressed.append(comp_doc)

        except Exception as e:
            print(f" > [LawRetriever] Failed to encode query: {e}")
            return "No relevant articles found."

        return"\n\n---\n\n".join(compressed)

    # - Build law index function (static) - #
    @staticmethod
    def extract_law_text(pdf_path: str) -> str:
        """ Extracts law text from law PDF """

        print(f" > [LawRetriever] Extracting text from {pdf_path}.")

        try:
            with fitz.open(pdf_path) as doc:
                pages_text = [page.get_text() for page in doc]
                text = "\n".join(pages_text)
    
                print(f" > [LawRetriever] Extracted {len(text)} chars.")
                return text
            
        except Exception as e:
            print(f" > [LawRetriever] Failed to extract text from PDF: {e}")
            return ""

    @staticmethod
    def split_into_articles(text: str) -> dict:
        """ Splits text into articles with RegEx """

        print(" > [LawRetriever] Splitting text into articles.")

        try:
            # Cleanup
            text = re.sub(r'[ \t]+', ' ', text)
            text = re.sub(r'\n{2,}', '\n', text)

            # RegEx match
            pattern = r'Article\s*(\d+(?:-\d+)?)\.\s*([^\n]*)\n(.*?)(?=Article\s*\d+(?:-\d+)?\.|\Z)'
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)

            # Extract articles
            articles = {}
            for num, title, content in matches:
                clean_content = re.sub(r'\s+', ' ', content.strip())
                if len(clean_content) < 10: # Treshold for non-informative lines
                    continue
                articles[num] = {
                    "title": title.strip(),
                    "content": clean_content
                }

            print(f" > [LawRetriever] Parsed {len(articles)} articles.")
            return articles

        except Exception as e:
            print(f" > [LawRetriever] Failed to split document: {e}")
            return {}

    @staticmethod
    def build_law_index():
        """ Builds law index """

        print(" > [Law index] Build started.")

        # Extract & validate text
        raw_text = LawRetriever.extract_law_text(settings.LAW_PDF_PATH)
        if not raw_text:
            print(" > [Law index] No text extracted, aborting.")
            return

        articles = LawRetriever.split_into_articles(raw_text)
        if not articles:
            print(" > [Law index] Parser didn't find any articles.")
            return

        print(f" > [Law index] Found {len(articles)} articles: {list(articles.keys())}")

        # Init objects
        embedder = SentenceTransformer(settings.SEN_TRANSFORMER_MODEL, device='cpu')
        client = chromadb.PersistentClient(path=settings.LAW_DB_PATH)

        # Reload collection
        try:
            client.delete_collection("housing_law")
        except Exception:
            pass
        collection = client.create_collection("housing_law")

        # Build & Save
        try:
            docs = [f"Article {num}: {v['title']}\n{v['content']}" for num, v in articles.items()]
            embeddings = embedder.encode(docs, normalize_embeddings=True).tolist()

            collection.add(
                documents=docs,
                embeddings=embeddings,
                ids=[f"art_{num}" for num in articles.keys()],
                metadatas=[{"article_num": num, "title": v['title']} for num, v in articles.items()]
            )
            print(f" > [Law index] Done. Saved in {settings.LAW_DB_PATH}.")

        except Exception as e:
            print(f" > [Law index] Failed to build embeddings: {e}")
            return

class AIService:
    """ AI tools & services class """

    def __init__(self, law_retriever: LawRetriever):
        print(" > [AIService] Init started.")

        # Groq client
        api_key = settings.GROQ_KEY
        self.client = Groq(api_key=api_key)

        # Law retriever
        self.retriever = law_retriever

        # Local variables
        self.config_dir = settings.LOGIC_CONF_DIR
        self.active_mode = None

        self._local_llm = None

        # Schema with explanations for LLM IN RUSSIAN (And convertion into string)
        self.finding_schema = {
            "clause_ref": "номер пункта договора, например '3.5' или '5.2'",
            "excerpt": "точная цитата из договора",
            "source": "статья закона, например 'Article 24, para 6' — обязательно, не оставлять пустым",
            "category": "одно из: responsibility | right | obligation | deadline | risk",
            "explanation": "что это значит для нанимателя простыми словами",
            "mitigation": "как переформулировать пункт по закону, или пустая строка если риска нет"
        }
        self.schema_str = json.dumps(self.finding_schema, ensure_ascii=False)

        print(" > [AIService] Init done.")

    @staticmethod
    def download_local_model():
        """ Checks & Downloads local LLM """

        model_path = settings.CENSOR_MODEL

        if os.path.exists(model_path):
            print(f" > [AIService] Model exists on path {model_path}.")
            return

        print(f" > [AIService] Downloading local LLM...")

        try:
            urllib.request.urlretrieve(
                settings.LLM_DOWNLOAD_URL,
                model_path
            )
            print("\n > [AIService] Model downloaded.")

        except Exception as e:
            if os.path.exists(model_path):
                os.remove(model_path)
            print(f"\n > [AIService] Model downloading error: {e}.")
            raise e

    # - Setters - #
    def _set_mode(self, mode: str = 'fast'):
        print(f" > [AIService] Setting mode: {mode}.")

        if mode not in settings.GROQ_MODELS:
            print(f" > [AIService] Unknown mode: {mode}. Set to default.")

        self.active_mode = mode

    # - Getters - #
    def _get_system_prompt(self, prompt_path: str) -> str:
        sys_prompt_path = os.path.join(self.config_dir, prompt_path)
        print(f" > [AIService] Reading prompt: {sys_prompt_path}.")

        if not os.path.exists(sys_prompt_path):
            print(f" > [AIService] Prompt file missing: {sys_prompt_path}.")
            raise FileNotFoundError(f"{sys_prompt_path} not found.")

        with open(sys_prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()

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
                return None

        return self._local_llm

    # - Internal functions - #
    def _apply_censor_replacements(self, text: str, entities: list) -> str:
        """ Applies censor replacements: Found entities replace with placeholders """

        print(" > [Censor] Applying replacements.")
        try:
            flat_occurrences = []

            valid_types = ("ФИО", "АДРЕС", "КОМПАНИЯ")

            # Extract & Validate entities
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

            # Apply RegEx (Long phrases first)
            flat_occurrences.sort(key=lambda pair: len(pair[0]), reverse=True)
            for occurrence, mask in flat_occurrences:
                if occurrence not in text:
                    print(f" > [Censor] Not found: {occurrence!r}")
                    continue

                text = text.replace(occurrence, mask)
                print(f" > [Censor] Replaced {occurrence!r} with {mask!r}.")

            print(f" > [Censor] Censored version: {text}")
            return text

        except Exception as e:
            print(f" > [Censor] Fatal error during censoring: {e}")
            return ""

    # - Public functions - #
    def censor(self, raw: str) -> str:
        """ Full censor function. Censors special elements: name, adress, company """

        print(" > [Censor] Censoring started.")
        
        # Prepare AI
        try:
            system_prompt = self._get_system_prompt("sys_prompt_censor.txt")

            llm = self._get_local_llm()
            if llm is None:
                return ""
        except Exception as e:
            print(f" > [Censor] Censor setup error: {e}. Returning empty string.")
            return ""

        # Censor
        user_message = (
            f"Текст документа:\n---\n{raw}\n---\n\n"
            f"Верни СТРОГО валидный JSON без пояснений.\n"
            f"От твоей работы зависит БЕЗОПАСНОСТЬ всех людей в тексте. Они РЕАЛЬНЫ."
        )
        max_retries = 3
        raw_output = "{}"

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

        # Parse result
        try: 
            parsed = json.loads(raw_output)
            entities = parsed.get("entities", [])
            print(f" > [Censor] Parsed {len(entities)} entities.")

            return self._apply_censor_replacements(raw, entities)

        except Exception as e:
            print(f" Incorrect JSON output: {raw_output}. Error: {e}")
            return ""

    def generate_analysis(self, report, mode: str):
        """ Generates document analytics with AI API """

        print(f" > [AI] Generating analysis in mode: {mode}.")

        # Get LLM mode
        self._set_mode(mode)
        model_name = settings.GROQ_MODELS[mode]

        # Validate report
        document_text = report.get("content", "") if isinstance(report, dict) else report
        if not document_text:
            print(" > [AI] Empty document text, aborting.")
            return None

        # Get law articles
        top_k = settings.LAW_ARTICLES[mode]
        try:
            law_context = self.retriever.find_relevant_articles(document_text, top_k=top_k)
        except Exception as e:
            print(f" > [AI] Failed to fetch law context: {e}")
            law_context = "No relevant articles found."

        # Prepare prompts
        user_message = (
            f"ЗАКОН:\n{law_context}\n\n"
            f"ДОГОВОР:\n{document_text}\n\n---\n"
            f"Пройди договор пункт за пунктом. Для каждой выявленной проблемы/риска создай отдельный объект в 'findings'.\n\n"
            f"ПРАВИЛА ДЛЯ 'source' (КРИТИЧЕСКИ ВАЖНО):\n"
            f"1. Твоя главная задача — найти статью из раздела ЗАКОН, которая хотя бы КОСВЕННО, по смыслу или теме относится к проверяемому пункту договора.\n"
            f"2. Если пункт договора касается оплаты, залога, выселения, ремонта или расторжения — В ЗАКОНЕ ПОЧТИ ВСЕГДА ЕСТЬ СООТВЕТСТВУЮЩАЯ СТАТЬЯ. Внимательно перечитай блок ЗАКОН.\n"
            f"3. Указывай номер статьи ТОЛЬКО из предоставленного текста ЗАКОНА (например, 'Статья 544' или 'Статья 24').\n"
            f"4. СТРОГО ЗАПРЕЩЕНО придумывать номера статей, которых НЕТ в блоке ЗАКОН.\n"
            f"5. Пиши 'не найдено в предоставленном законе' ТОЛЬКО в самом крайнем случае, если в блоке ЗАКОН вообще нет ни одного упоминания этой темы.\n\n"

            f"ПРАВИЛА ДЛЯ 'mitigation':\n"
            f"- Для категории 'risk' или для очевидно неадекватных условий/сумм — ОБЯЗАТЕЛЬНО предложи конкретную юридически корректную формулировку для исправления.\n"
            f"- Для остальных категорий — предложи улучшение текста договора.\n\n"

            f"ОГРАНИЧЕНИЕ ОБЛАСТИ:\n"
            f"Если документ вообще не является договором аренды/жилищным правом — верни {{\"findings\": []}}.\n\n"
            f"Формат ответа:\n{self.schema_str}\n\n"
            f"Отвечай СТРОГО в формате JSON: {{\"findings\": [ ... ]}}"
        )

        try:
            system_prompt = self._get_system_prompt(f"sys_prompt_{self.active_mode}.txt")
        except Exception as e:
            print(f" > [AI] Failed to load system prompt: {e}")
            return None

        # Try to get an analysis from API
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
        print(" > [DocProcessor] Initted.")

    def _preprocess_file(self, ai_service: AIService, file_text: str) -> str:
        print(" > [DocProcessor] Preprocessing file.")

        preprocessed = ai_service.censor(file_text)

        #print(f" > -------------- Result: {preprocessed} -------------- <")
        print(" > [DocProcessor] Censoring done.")
        return {"content": preprocessed}

    def _main_process(self, ai_service: AIService, user: dict, doc_text: str) -> str:
        print(" > [DocProcessor] Main process started.")

        used_model = "smart" if user["tier"] == "premium" else "fast"

        return ai_service.generate_analysis(doc_text, used_model)

    def analyze(self, text: str, user: dict) -> str:
        """ Main document analyze cycle """

        print(" > [DocProcessor] Analyze called.")
        
        try:
            # Init
            retriever = LawRetriever()
            ai_service = AIService(retriever)

            # Preprocess file
            raw_dict = self._preprocess_file(ai_service, text)

            # Analyze file
            result = self._main_process(ai_service, user, raw_dict)

            print(" > [DocProcessor] Analyze finished.")
            #print(f" > Final: {result}")
            return result

        except Exception as e:
            print(f"Analyze error. Maybe, something is not set. Error: {e}")
            return ""
