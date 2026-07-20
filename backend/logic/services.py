""" Main app business logic """

import os
import re

import time
import json

import fitz
import chromadb

from sentence_transformers import SentenceTransformer
from groq import Groq, RateLimitError, APIStatusError

from llama_cpp import Llama

import core.settings as settings

#from .models import Report

class LawRetriever:
    def __init__(self):
        self.embedder = SentenceTransformer(settings.SEN_TRANSFORMER_MODEL, device='cpu')
        self.db_client = chromadb.PersistentClient(path=settings.LAW_DB_PATH)

        try:
            self.collection = self.db_client.get_collection("housing_law")
        except Exception:
            raise RuntimeError(
                f"Law database not found at {settings.LAW_DB_PATH}."
                f"Run build_law_index() before use."
            )

    def find_relevant_articles(self, document_text, top_k=5) -> str:
        query_embedding = self.embedder.encode(
            [document_text[:2000]], normalize_embeddings=True
        ).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
        if not results['documents'] or not results['documents'][0]:
            return "No relevant articles found."
        return "\n\n---\n\n".join(results['documents'][0])
    
    def extract_law_text(self, pdf_path) -> str:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text

    def split_into_articles(self, text) -> dict:
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{2,}', '\n', text)

        pattern = r'Article\s*(\d+(?:-\d+)?)\.\s*([^\n]*)\n(.*?)(?=Article\s*\d+(?:-\d+)?\.|\Z)'
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)

        articles = {}
        for num, title, content in matches:
            clean_content = re.sub(r'\s+', ' ', content.strip())
            if len(clean_content) < 10:
                continue
            articles[num] = {
                "title": title.strip(),
                "content": clean_content
            }
        return articles

    def build_law_index(self):
        raw_text = self.extract_law_text(settings.LAW_PDF_PATH)
        articles = self.split_into_articles(raw_text)

        if not articles:
            print("[Law index] Parser didn't find any articles.")
            return

        print(f"[Law index] Found {len(articles)} articles: {list(articles.keys())}")

        embedder = SentenceTransformer(settings.SEN_TRANSFORMER_MODEL, device='cpu')

        client = chromadb.PersistentClient(path=settings.LAW_DB_PATH)
        try:
            client.delete_collection("housing_law")
        except Exception:
            pass
        collection = client.create_collection("housing_law")

        docs = [f"Article {num}: {v['title']}\n{v['content']}" for num, v in articles.items()]
        embeddings = embedder.encode(docs, normalize_embeddings=True).tolist()

        collection.add(
            documents=docs,
            embeddings=embeddings,
            ids=[f"art_{num}" for num in articles.keys()],
            metadatas=[{"article_num": num, "title": v['title']} for num, v in articles.items()]
        )

        print(f"[Law index] Done. Saved in {settings.LAW_DB_PATH}.")

class CensorshipError(Exception):
    """ Error catcher """

class AIService:
    def __init__(self):
        api_key = settings.GROQ_KEY
        self.client = Groq(api_key=api_key)
        self.config_dir = settings.LOGIC_CONF_DIR
        self.active_mode = None
        self.retriever = LawRetriever()

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

    def _set_mode(self, mode: str):
        if mode not in settings.GROQ_MODELS:
            raise ValueError(f"Unknown mode: {mode}.")
        self.active_mode = mode

    def _get_analyzer_system_prompt(self) -> str:
        sys_prompt_path = os.path.join(self.config_dir, f"sys_prompt_{self.active_mode}.txt")
        if not os.path.exists(sys_prompt_path):
            raise FileNotFoundError(f"{sys_prompt_path} not found.")

        with open(sys_prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()

    def _get_censor_system_prompt(self) -> str:
        sys_prompt_path = os.path.join(self.config_dir, "sys_prompt_censor.txt")

        if not os.path.exists(sys_prompt_path):
            raise FileNotFoundError(f"{sys_prompt_path} not found.")

        with open(sys_prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()

    def _get_local_llm(self) -> Llama:
        if self._local_llm is None:
            print(f"[Censor] Loading local LLM: {settings.CENSOR_MODEL}")
            self._local_llm = Llama(
                model_path=str(settings.CENSOR_MODEL),
                n_ctx=4096,
                verbose=False,
            )
        return self._local_llm

    def censor(self, raw: str) -> str:
        """ Name, adress, company, subscription -> Placeholders """
        system_prompt = self._get_censor_system_prompt()
        llm = self._get_local_llm()
 
        user_message = (
            f"Текст документа:\n---\n{raw}\n---\n\n"
            f"Верни СТРОГО валидный JSON без пояснений, в формате:\n"
            f'{{"entities": [{{"canonical": "...", "occurrences": ["..."], "type": "ФИО"}}]}}'
        )

        max_retries = 3
        raw_output = None

        for attempt in range(max_retries):
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
                break
            except Exception as e:
                print(f"[Censor] Model error ({attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise CensorshipError(f"Local LLM unavailable: {e}") from e

        try:
            parsed = json.loads(raw_output)
            entities = parsed.get("entities", [])
        except (json.JSONDecodeError, AttributeError) as e:
            raise CensorshipError(f"Invalid JSON: {raw_output!r}") from e
 
        return self._apply_censor_replacements(raw, entities)

    def _apply_censor_replacements(self, text: str, entities: list) -> str:
        history = {"fio": {}, "address": {}}
        counters = {"fio": 1, "address": 1}
        flat_occurrences = []
 
        for entity in entities:
            canonical = entity.get("canonical")
            entity_type = entity.get("type")
            occurrences = entity.get("occurrences", [])

            if not canonical or entity_type not in ("ФИО", "АДРЕС", "ПОДПИСЬ", "КОМПАНИЯ") or not occurrences:
                continue  # Filter entities

            history_key = "fio" if entity_type == "ФИО" else "address"

            dedup_key = canonical.strip().lower()
            if dedup_key not in history[history_key]:
                history[history_key][dedup_key] = counters[history_key]
                counters[history_key] += 1

            placeholder = f"[{entity_type}_{history[history_key][dedup_key]}]"
 
            for occurrence in occurrences:
                if not isinstance(occurrence, str) or not occurrence.strip():
                    continue
                flat_occurrences.append((occurrence, placeholder))

        # Long phrases first
        flat_occurrences.sort(key=lambda pair: len(pair[0]), reverse=True)

        for occurrence, placeholder in flat_occurrences:
            if occurrence not in text:
                print(f"[Censor] Not found: {occurrence!r}")
                continue
            text = text.replace(occurrence, placeholder)

        return text

    def generate_analysis(self, report, mode: str = 'fast'):
        self._set_mode(mode)
        model_name = settings.GROQ_MODELS[mode]
        document_text = report.get("content", "") if isinstance(report, dict) else report
 
        top_k = 4 if mode == 'fast' else 8
        law_context = self.retriever.find_relevant_articles(document_text, top_k=top_k)
        schema_str = json.dumps(self.finding_schema, ensure_ascii=False)

        user_message = (
            f"ЗАКОН (English source, cite exact Article number in 'source' for every finding):\n"
            f"{law_context}\n\n"
            f"ДОГОВОР:\n"
            f"{document_text}\n\n"
            f" ----------------- "
            f"Пройди договор пункт за пунктом. Для каждого пункта, где есть обязательство, право, "
            f"риск или дедлайн - создай отдельный объект findings. Не объединяй разные пункты в один.\n"
            f"ОБЯЗАТЕЛЬНО: поле 'source' должно содержать конкретный номер статьи из блока ЗАКОН выше. "
            f"Если ни одна статья не применима к пункту - напиши 'не найдено в предоставленном законе', "
            f"не придумывай номер.\n\n"
            f"Формат каждого объекта в массиве findings:\n{schema_str}\n\n"
            f"Верни JSON: {{\"findings\": [ ... ]}}"
        )

        system_prompt = self._get_analyzer_system_prompt()

        max_retries = 3
        for attempt in range(max_retries):
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
                return completion.choices[0].message.content
            except (RateLimitError, APIStatusError) as e:
                if attempt < max_retries - 1:
                    wait = 15 * (attempt + 1)
                    print(f"[AI] Rate limit, wiit {wait}s...")
                    time.sleep(wait)
                    continue
                print(f"[AI] Critical error (timeout): {e}")
                return None
            except Exception as e:
                print(f"[AI] Critical error: {e}")
                return None

class DocumentProcessor:
    def __init__(self):
        self.ai_service = AIService()

    def _preprocess_file(self, file_text) -> dict:
        preprocessed = self.ai_service.censor(file_text)
        print(preprocessed)
        return {"content": preprocessed}

    def _main_process(self, user, file_dict) -> dict:
        used_model = "smart" if user["tier"] == "premium" else "fast"
        return self.ai_service.generate_analysis(file_dict, used_model)

    def send_front(self, res):
        ...

    def analyze(self, text, user) -> str:
        raw_dict = self._preprocess_file(text)
        result = self._main_process(user, raw_dict)
        self.send_front(result)
        return result
