import json
import re
from pathlib import Path
import fire
import bm25s
import Stemmer
from pydantic import BaseModel

CHUNKS_FILE = Path("data/processed/chunks.json")


class MinimalSource(BaseModel):
    file_path: str
    first_character_index: int
    last_character_index: int


def load_chunks(chunks_file: Path = CHUNKS_FILE) -> list[dict]:
    if not chunks_file.exists():
        raise FileNotFoundError(
            f"Missing {chunks_file}; run python3 -m src.main first."
        )
    chunks = json.loads(chunks_file.read_text(encoding="utf-8"))
    if not chunks:
        raise ValueError("Chunk file is empty")
    return chunks


def load_questions(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return data.get("rag_questions", data.get("questions", []))


def code_tokenize_text(text: str) -> list[str]:
    """Splits camelCase/PascalCase and snake_case while preserving full identifiers."""
    expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    expanded = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", expanded)

    parts = re.findall(r"[a-zA-Z0-9]+", expanded.lower())
    snake = re.findall(r"[a-zA-Z0-9]+(?:_[a-zA-Z0-9]+)+", text.lower())
    return parts + snake


def _build_code_doc_text(chunk: dict) -> str:
    fpath = chunk["file_path"]
    path_parts = re.split(r"[/._-]+", fpath.lower())
    path_hint = " ".join(p for p in path_parts if p)
    content = chunk.get("indexed_text", chunk["content"])
    return f"{path_hint} {path_hint}\n{content}"


def search_dataset(
    dataset_path: str,
    k: int = 10,
    save_directory: str = "data/processed",
    chunks_file: str = "data/processed/chunks.json",
) -> None:
    ds_path = Path(dataset_path)
    if not ds_path.exists():
        raise FileNotFoundError(f"Dataset path {dataset_path} does not exist.")

    if ds_path.is_dir():
        for jf in sorted(ds_path.glob("*.json")):
            search_dataset(
                dataset_path=str(jf),
                k=k,
                save_directory=save_directory,
                chunks_file=chunks_file,
            )
        return

    chunks = load_chunks(Path(chunks_file))
    is_doc_dataset = "doc" in ds_path.name.lower()

    if is_doc_dataset:
        filtered_chunks = [
            c for c in chunks if c["file_path"].lower().endswith((".md", ".txt"))
        ]
    else:
        filtered_chunks = [
            c for c in chunks if c["file_path"].lower().endswith(".py")
        ]

    if not filtered_chunks:
        filtered_chunks = chunks

    questions = load_questions(ds_path)
    search_results = []

    if is_doc_dataset:
        corpus = [
            f"File: {c['file_path']}\n{c.get('indexed_text', c['content'])}"
            for c in filtered_chunks
        ]
        stemmer = Stemmer.Stemmer("english")
        corpus_tokens = bm25s.tokenize(corpus, stopwords="en", stemmer=stemmer)
        retriever = bm25s.BM25()
        retriever.index(corpus_tokens)

        for item in questions:
            question = str(item.get("question", item.get("text", ""))).strip()
            if not question:
                continue
            qid = str(item.get("question_id", item.get("id", "q_unknown")))
            q_tokens = bm25s.tokenize(question, stemmer=stemmer)
            results, scores = retriever.retrieve(
                q_tokens, k=min(k, len(filtered_chunks))
            )

            sources = []
            for rank in range(results.shape[1]):
                chunk_idx = int(results[0, rank])
                if float(scores[0, rank]) <= 0:
                    continue
                chunk = filtered_chunks[chunk_idx]
                sources.append(
                    MinimalSource(
                        file_path=chunk["file_path"],
                        first_character_index=chunk["first_character_index"],
                        last_character_index=chunk["last_character_index"],
                    ).model_dump()
                )

            search_results.append(
                {
                    "question_id": qid,
                    "question": question,
                    "retrieved_sources": sources,
                }
            )
    else:
        corpus = [_build_code_doc_text(c) for c in filtered_chunks]
        corpus_tokens = [code_tokenize_text(doc) for doc in corpus]
        retriever = bm25s.BM25(k1=1.5, b=0.75)
        retriever.index(corpus_tokens)

        fetch_k = min(len(filtered_chunks), max(k * 2, 20))

        for item in questions:
            question = str(item.get("question", item.get("text", ""))).strip()
            if not question:
                continue
            qid = str(item.get("question_id", item.get("id", "q_unknown")))

            q_tokens = code_tokenize_text(question)
            results, scores = retriever.retrieve([q_tokens], k=fetch_k)

            ranked: list[tuple[float, int]] = []
            for rank in range(results.shape[1]):
                chunk_idx = int(results[0, rank])
                score = float(scores[0, rank])
                if score <= 0:
                    continue
                fpath = filtered_chunks[chunk_idx]["file_path"].replace("\\", "/")
                if "/tests/" in fpath or fpath.startswith("tests/"):
                    score *= 0.85
                ranked.append((score, chunk_idx))

            ranked.sort(key=lambda x: x[0], reverse=True)

            sources = []
            for _, chunk_idx in ranked[:k]:
                chunk = filtered_chunks[chunk_idx]
                sources.append(
                    MinimalSource(
                        file_path=chunk["file_path"],
                        first_character_index=chunk["first_character_index"],
                        last_character_index=chunk["last_character_index"],
                    ).model_dump()
                )

            search_results.append(
                {
                    "question_id": qid,
                    "question": question,
                    "retrieved_sources": sources,
                }
            )

    payload = {"search_results": search_results, "k": k}
    out_target = Path(save_directory)
    out_file = (
        out_target
        if out_target.suffix == ".json"
        else out_target / f"search_treesitter_{ds_path.name}"
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Saved student_search_results to {out_file}")


if __name__ == "__main__":
    fire.Fire({"search_dataset": search_dataset})