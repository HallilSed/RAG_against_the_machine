import json
import math
import re
import Stemmer
from pydantic import BaseModel
from pathlib import Path

CHUNKS_FILE = Path("data/processed/chunks.json")

class MinimalSource(BaseModel):
    file_path: str
    first_character_index: int
    last_character_index: int

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
        
        (
            self.docs_doc_length,
            self.docs_avgdl,
            self.docs_token_to_id,
        ) = self.build_corpus_stats(docs_tokenized)
        
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