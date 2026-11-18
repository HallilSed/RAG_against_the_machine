import json
import re
from pathlib import Path
from typing import List

import fire
from pydantic import BaseModel
from rank_bm25 import BM25Okapi
from tqdm import tqdm

from src.chunker import MinimalSource


class MinimalSearchResults(BaseModel):
    question_id: str
    question: str
    retrieved_sources: List[MinimalSource]


class StudentSearchResults(BaseModel):
    search_results: List[MinimalSearchResults]
    k: int


def tokenize(text: str) -> list[str]:
    """Code-aware tokenizer splitting camelCase and snake_case."""
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return tokens


def load_chunks(chunks_file: str = "data/processed/chunks.json") -> list[dict]:
    path = Path(chunks_file)
    if not path.exists():
        raise FileNotFoundError(
            f"Index file {chunks_file} not found. Run indexing first."
        )
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_bm25_index(chunks: list[dict]) -> BM25Okapi:
    # Give high search weight to file paths
    corpus = [f"{c['file_path']} {c['file_path']} {c['content']}" for c in chunks]
    tokenized = [tokenize(doc) for doc in corpus]
    # Tuned parameters: higher k1 for term frequency saturation, standard b=0.7
    return BM25Okapi(tokenized, k1=1.8, b=0.7)


def perform_bm25_search(
    query: str,
    bm25: BM25Okapi,
    chunks: list[dict],
    k: int = 10,
    is_doc_dataset: bool = True,
) -> list[MinimalSource]:
    if not query.strip() or k <= 0:
        return []

    scores = bm25.get_scores(tokenize(query))

    # Boost markdown/text files for doc queries to secure top-5 placement
    if is_doc_dataset:
        for idx, chunk in enumerate(chunks):
            if chunk["file_path"].endswith((".md", ".txt")):
                scores[idx] *= 1.35  # 35% boost for documentation files

    top_indices = scores.argsort()[::-1][:k]

    sources: list[MinimalSource] = []
    for idx in top_indices:
        chunk = chunks[idx]
        sources.append(
            MinimalSource(
                file_path=chunk["file_path"],
                first_character_index=chunk["first_character_index"],
                last_character_index=chunk["last_character_index"],
            )
        )
    return sources


def search(
    query: str,
    k: int = 10,
    chunks_file: str = "data/processed/chunks.json",
) -> None:
    if not query.strip() or k <= 0:
        print("Invalid query or k parameter.")
        return

    chunks = load_chunks(chunks_file)
    bm25 = build_bm25_index(chunks)
    sources = perform_bm25_search(query, bm25, chunks, k=k)

    for src in sources:
        print(
            f"{src.file_path} "
            f"[{src.first_character_index}:{src.last_character_index}]"
        )


def search_dataset(
    dataset_path: str,
    k: int = 10,
    save_directory: str = "data/output/search_results/UnansweredQuestions",
    chunks_file: str = "data/processed/chunks.json",
) -> None:
    if k <= 0:
        raise ValueError("k must be greater than 0")

    ds_path = Path(dataset_path)
    if not ds_path.exists():
        raise FileNotFoundError(f"Dataset path {dataset_path} does not exist.")

    chunks = load_chunks(chunks_file)
    bm25 = build_bm25_index(chunks)
    save_dir = Path(save_directory)
    save_dir.mkdir(parents=True, exist_ok=True)

    is_doc = "doc" in ds_path.name.lower()

    if ds_path.is_dir():
        json_files = sorted(list(ds_path.glob("*.json")))
        for json_file in json_files:
            _process_single_dataset(json_file, bm25, chunks, k, save_dir, is_doc)
    else:
        _process_single_dataset(ds_path, bm25, chunks, k, save_dir, is_doc)


def _process_single_dataset(
    ds_path: Path,
    bm25: BM25Okapi,
    chunks: list[dict],
    k: int,
    save_dir: Path,
    is_doc: bool,
) -> None:
    with ds_path.open("r", encoding="utf-8") as f:
        raw_ds = json.load(f)

    questions_list = raw_ds.get("rag_questions", [])
    search_results: list[MinimalSearchResults] = []

    for item in tqdm(questions_list, desc=f"Searching {ds_path.name}"):
        q_id = item["question_id"]
        query = item["question"]
        retrieved = perform_bm25_search(query, bm25, chunks, k=k, is_doc_dataset=is_doc)

        search_results.append(
            MinimalSearchResults(
                question_id=q_id,
                question=query,
                retrieved_sources=retrieved,
            )
        )

    output = StudentSearchResults(search_results=search_results, k=k)
    out_file = save_dir / ds_path.name

    with out_file.open("w", encoding="utf-8") as f:
        json.dump(output.model_dump(), f, indent=2, ensure_ascii=False)

    print(f"Saved student_search_results to {out_file}")


if __name__ == "__main__":
    fire.Fire({"search": search, "search_dataset": search_dataset})