import json
from pathlib import Path
from pydantic import BaseModel
from rank_bm25 import BM25Okapi

CHUNKS_PATH = Path("data/processed/chunks.json")

class MinimalSource(BaseModel):
    file_path: str
    first_character_index: int
    last_character_index: int

class MinimalSearchResults(BaseModel):
    question_id: str
    question: str
    retrieved_sources: list[MinimalSource]

def load_chunks():
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(f"{CHUNKS_PATH} not found. Run chunking first!")
    with CHUNKS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def search(query: str, question_id: str = "q_test", top_k: int = 5) -> MinimalSearchResults:
    chunks = load_chunks()
    
    # Simple tokenization
    corpus = [c["content"].lower().split() for c in chunks]
    bm25 = BM25Okapi(corpus)
    
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)
    
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    
    retrieved_sources = [
        MinimalSource(
            file_path=chunks[idx]["file_path"],
            first_character_index=chunks[idx]["first_character_index"],
            last_character_index=chunks[idx]["last_character_index"],
        )
        for idx in top_indices
    ]
    
    return MinimalSearchResults(
        question_id=question_id,
        question=query,
        retrieved_sources=retrieved_sources
    )

if __name__ == "__main__":
    import sys
    query_text = sys.argv[1] if len(sys.argv) > 1 else "LLMEngine class"
    result = search(query_text)
    print(result.model_dump_json(indent=2))