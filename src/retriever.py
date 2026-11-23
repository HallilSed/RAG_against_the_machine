import argparse
import json
from pathlib import Path
from typing import Any, Literal
from pydantic import BaseModel
from src.my_indexer import CHUNKS_FILE, Index

CODE_EXTENSION: set[str] = {".py"}
DOCS_EXTENSION: set[str] = {".md", ".txt"}
CorpusType = Literal["code", "docs"]


class MinimalSource(BaseModel):
    file_path: str
    first_character_index: int
    last_character_index: int


class Retriever:
    def __init__(self, index: Index | None = None, chunks_file: Path = CHUNKS_FILE) -> None:
        self.index = index if index is not None else Index()
        if not hasattr(self.index, "code_postings"):
            self.index.filter_docs(chunks_file)


    def _get_corpus_state(self, corpus_type: CorpusType):
        if corpus_type == "code":
            return (
                self.index.code_tokenizer,
                self.index.code_token_to_id,
                self.index.code_postings,
                self.index.code_chunks,
            )
        if corpus_type == "docs":
            return (
                self.index.docs_tokenizer,
                self.index.docs_token_to_id,
                self.index.docs_postings,
                self.index.doc_chunks,
            )
        raise ValueError(f"Unsupported corpus_type: {corpus_type}")

    def retrieve(self, query: str, corpus_type: CorpusType = "code", k: int = 10) -> list[dict]:

        if not query or not query.strip() or k <= 0:
            return []

        tokenizer, token_to_id, postings, chunks = self._get_corpus_state(corpus_type)
        if not chunks or not postings or not token_to_id:
            return []

        query_tokens = tokenizer(query)
        scores: list[float] = [0.0] * len(chunks)

        for q_tok in query_tokens:
            token_id = token_to_id.get(q_tok)
            if token_id is None:
                continue
            for doc_id, term_score in postings.get(token_id, []):
                scores[doc_id] += term_score

        ranked: list[tuple[float, int]] = [
            (score, doc_id)
            for doc_id, score in enumerate(scores)
            if score > 0.0
        ]
        ranked.sort(key=lambda item: item[0], reverse=True)

        results: list[dict] = []
        for _, doc_id in ranked[:k]:
            chunk = chunks[doc_id]
            results.append(
                MinimalSource(
                    file_path=chunk["file_path"],
                    first_character_index=chunk["first_character_index"],
                    last_character_index=chunk["last_character_index"],
                ).model_dump()
            )

        return results

    @staticmethod
    def _infer_corpus_type(dataset_path: Path, explicit: CorpusType | None = None) -> CorpusType:
        if explicit is not None:
            return explicit
        name = dataset_path.name.lower()
        if "doc" in name:
            return "docs"
        return "code"

    @staticmethod
    def _extract_query(item: str | dict[str, Any]) -> str:
        if isinstance(item, str):
            if item.strip():
                return item
            raise ValueError("Dataset contains an empty query string")
        if isinstance(item, dict):
            for key in ("question", "query", "prompt", "instruction"):
                val = item.get(key)
                if isinstance(val, str) and val.strip():
                    return val
        raise KeyError(f"Could not find query text in dataset item: {item!r}")

    def search_dataset(
        self,
        dataset_path: Path,
        k: int = 10,
        save_directory: Path | None = None,
        corpus_type: CorpusType | None = None,
    ) -> list[dict[str, Any]]:
        if not dataset_path.exists():
            raise FileNotFoundError(f"Missing dataset: {dataset_path}")

        resolved_corpus = self._infer_corpus_type(dataset_path, corpus_type)
        items = json.loads(dataset_path.read_text(encoding="utf-8"))

        outputs: list[dict[str, Any]] = []
        for item in items:
            query = self._extract_query(item)
            hits = self.retrieve(query=query, corpus_type=resolved_corpus, k=k)
            if isinstance(item, dict):
                record = dict(item)
                record["retrieved_sources"] = hits
            else:
                record = {
                    "query": query,
                    "retrieved_sources": hits,
                }
            outputs.append(record)

        if save_directory is not None:
            out_path = Path(save_directory)
            if out_path.suffix.lower() == ".json":
                out_path.parent.mkdir(parents=True, exist_ok=True)
                target_file = out_path
            else:
                out_path.mkdir(parents=True, exist_ok=True)
                target_file = out_path / f"{dataset_path.stem}_results.json"

            target_file.write_text(json.dumps(outputs, indent=2), encoding="utf-8")

        return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="BM25 Retriever CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_cmd = subparsers.add_parser("search_dataset", help="Run retrieval over a dataset JSON")
    search_cmd.add_argument("--dataset_path", type=Path, required=True)
    search_cmd.add_argument("--k", type=int, default=10)
    search_cmd.add_argument("--save_directory", type=Path, required=True)
    search_cmd.add_argument("--chunks_file", type=Path, default=CHUNKS_FILE)
    search_cmd.add_argument("--corpus_type", choices=["code", "docs"], default=None)

    args = parser.parse_args()

    if args.command == "search_dataset":
        idx = Index()
        idx.filter_docs(args.chunks_file)
        retriever = Retriever(index=idx)
        retriever.search_dataset(
            dataset_path=args.dataset_path,
            k=args.k,
            save_directory=args.save_directory,
            corpus_type=args.corpus_type,
        )


if __name__ == "__main__":
    main()