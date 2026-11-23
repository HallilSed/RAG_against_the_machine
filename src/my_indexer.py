from collections import Counter
import json
import math
from pathlib import Path
import re
from pydantic import BaseModel
import Stemmer

CHUNKS_FILE = Path("data/processed/chunks.json")


STOPWORDS: set[str] = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an",
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about",
    "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where",
    "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"
}


class Index:

    def __init__(self):
        self._stemmer = Stemmer.Stemmer("english")

    def load_document(self, chunks_file: Path = CHUNKS_FILE) -> list[dict]:
        if not chunks_file.exists():
            raise FileNotFoundError(f"Missing {chunks_file}")

        with open(chunks_file, "r", encoding="utf-8") as file:
            chunks = json.load(file)

        if not chunks:
            raise ValueError(f"{chunks_file} file is empty")

        return chunks

    def code_tokenizer(self, text: str) -> list[str]:
        expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
        exp_prev = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", expanded)

        parts = re.findall(r"[a-zA-Z0-9]+", exp_prev.lower())
        snake = re.findall(r"[a-zA-Z0-9]+(?:_[a-zA-Z0-9]+)+", text.lower())

        return parts + snake

    def docs_tokenizer(self, text: str) -> list[str]:
        words = re.findall(r"[a-z0-9]+", text.lower())
        filtered = [word for word in words if word not in STOPWORDS]

        return self._stemmer.stemWords(filtered)

    @staticmethod
    def build_corpus_stats(tokenized_docs: list[list[str]]) -> tuple[list[int], float, dict[str, int]]:
        doc_lengths = [len(tokens) for tokens in tokenized_docs]
        avgdl = (sum(doc_lengths) / len(doc_lengths)) if doc_lengths else 0.0

        token_to_id: dict[str, int] = {}

        for tokens in tokenized_docs:
            for token in tokens:
                if token not in token_to_id:
                    token_to_id[token] = len(token_to_id)

        return doc_lengths, avgdl, token_to_id

    def compute_idf(self, tokenized_docs: list[list[str]], token_to_id: dict[str, int]) -> list[float]:
        n_docs = len(tokenized_docs)

        if n_docs == 0 or not token_to_id:
            return []

        df: dict[str, int] = {tok: 0 for tok in token_to_id}

        for tokens in tokenized_docs:
            for token in set(tokens):
                df[token] += 1

        idf_scores: list[float] = [0.0] * len(token_to_id)

        for token, token_id in token_to_id.items():
            doc_freq = df[token]
            idf = math.log((n_docs - doc_freq + 0.5) / (doc_freq + 0.5))
            idf_scores[token_id] = idf

        return idf_scores

    def bm25_index(
        self,
        tokenized_docs: list[list[str]],
        doc_lengths: list[int],
        avgdl: float,
        token_to_id: dict[str, int],
        idf_scores: list[float],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> dict[int, list[tuple[int, float]]]:
        if not tokenized_docs or avgdl <= 0 or not token_to_id:
            return {}

        posting: dict[int, list[tuple[int, float]]] = {t_id: [] for t_id in token_to_id.values()}

        for doc_id, tokens in enumerate(tokenized_docs):
            tf_counts = Counter(tokens)
            doc_len = doc_lengths[doc_id]
            norm = 1.0 - b + b * (doc_len / avgdl)
            for tok, tf in tf_counts.items():
                token_id = token_to_id[tok]
                idf = idf_scores[token_id]
                score = idf * ((tf * (k1 + 1.0)) / (tf + k1 * norm))
                posting[token_id].append((doc_id, score))

        return posting

    def filter_docs(self, chunks_file: Path = CHUNKS_FILE) -> None:
        code_tokenized: list[list[str]] = []
        code_chunks: list[dict] = []

        docs_tokenized: list[list[str]] = []
        doc_chunks: list[dict] = []

        chunks = self.load_document(chunks_file)

        for chunk in chunks:
            suffix = Path(chunk["file_path"]).suffix.lower()
            text = chunk.get("indexed_text") or chunk["content"]

            if suffix == ".py":
                code_chunks.append(chunk)
                code_tokenized.append(self.code_tokenizer(text))
            elif suffix in {".md", ".txt"}:
                doc_chunks.append(chunk)
                docs_tokenized.append(self.docs_tokenizer(text))

        self.code_chunks = code_chunks
        self.doc_chunks = doc_chunks
        self.code_tokenized = code_tokenized
        self.docs_tokenized = docs_tokenized

        (
            self.code_doc_length,
            self.code_avgdl,
            self.code_token_to_id,
        ) = self.build_corpus_stats(code_tokenized)
        self.code_idf = self.compute_idf(code_tokenized, self.code_token_to_id)
        self.code_postings = self.bm25_index(
            code_tokenized,
            self.code_doc_length,
            self.code_avgdl,
            self.code_token_to_id,
            self.code_idf,
        )

        (
            self.docs_doc_length,
            self.docs_avgdl,
            self.docs_token_to_id,
        ) = self.build_corpus_stats(docs_tokenized)
        self.docs_idf = self.compute_idf(docs_tokenized, self.docs_token_to_id)
        self.docs_postings = self.bm25_index(
            docs_tokenized,
            self.docs_doc_length,
            self.docs_avgdl,
            self.docs_token_to_id,
            self.docs_idf,
        )