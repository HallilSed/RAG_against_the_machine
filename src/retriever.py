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

    def retrieve(
        self,
        query: str,
        corpus_type: CorpusType = "code",
        k: int = 10,
    ) -> list[dict]:
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
        if "doc" in dataset_path.name.lower():
            return "docs"
        return "code"

    @staticmethod
    def _load_questions(path: Path) -> list[Any]:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("rag_questions", data.get("questions", []))
        return []

    @staticmethod
    def _parse_question_item(item: Any, fallback_idx: int) -> tuple[str, str] | None:
        if isinstance(item, str):
            question = item.strip()
            if not question:
                return None
            return f"q_{fallback_idx}", question

        if isinstance(item, dict):
            question = str(item.get("question", item.get("text", item.get("query", "")))).strip()
            if not question:
                return None
            qid = str(item.get("question_id", item.get("id", f"q_{fallback_idx}")))
            return qid, question

        return None

    def search_dataset(
        self,
        dataset_path: str | Path,
        k: int = 10,
        save_directory: str | Path = "data/processed",
        corpus_type: CorpusType | None = None,
    ) -> dict[str, Any]:
        ds_path = Path(dataset_path)
        if not ds_path.exists():
            raise FileNotFoundError(f"Dataset path {dataset_path} does not exist.")

        if ds_path.is_dir():
            last_payload: dict[str, Any] = {"search_results": [], "k": k}
            for jf in sorted(ds_path.glob("*.json")):
                last_payload = self.search_dataset(
                    dataset_path=jf,
                    k=k,
                    save_directory=save_directory,
                    corpus_type=corpus_type,
                )
            return last_payload

        resolved_corpus = self._infer_corpus_type(ds_path, corpus_type)
        items = self._load_questions(ds_path)

        search_results: list[dict[str, Any]] = []
        for idx, item in enumerate(items, start=1):
            parsed = self._parse_question_item(item, idx)
            if parsed is None:
                continue
            qid, question = parsed
            sources = self.retrieve(query=question, corpus_type=resolved_corpus, k=k)
            search_results.append(
                {
                    "question_id": qid,
                    "question": question,
                    "retrieved_sources": sources,
                }
            )

        payload: dict[str, Any] = {
            "search_results": search_results,
            "k": k,
        }

        out_target = Path(save_directory)
        out_file = (
            out_target
            if out_target.suffix.lower() == ".json"
            else out_target / f"search_treesitter_{ds_path.name}"
        )
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Saved student_search_results to {out_file}")
        return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="BM25 Retriever CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_cmd = subparsers.add_parser("search_dataset", help="Run retrieval over a dataset JSON")
    search_cmd.add_argument("--dataset_path", type=Path, required=True)
    search_cmd.add_argument("--k", type=int, default=10)
    search_cmd.add_argument("--save_directory", type=Path, default=Path("data/processed"))
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