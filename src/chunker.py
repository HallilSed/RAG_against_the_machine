from pathlib import Path
from pydantic import BaseModel


class MinimalSource(BaseModel):
    file_path: str
    first_character_index: int
    last_character_index: int


class ChunkResult(MinimalSource):
    content: str


class Chunker:
    def __init__(self, max_chunk_size: int = 2000) -> None:
        self.max_chunk_size = max_chunk_size
        self.all_chunks: list[ChunkResult] = []

    def _add_chunk(
        self, file_path: str, start: int, end: int, content: str
    ) -> None:
        if not content.strip():
            return

        # Enforce hard context cap
        if len(content) > self.max_chunk_size:
            content = content[: self.max_chunk_size]
            end = start + len(content)

        self.all_chunks.append(
            ChunkResult(
                file_path=file_path,
                first_character_index=start,
                last_character_index=end,
                content=content,
            )
        )

    def _sliding_window(
        self, text: str, offset: int, file_path: str, chunk_size: int = 1800, overlap: int = 500
    ) -> None:
        step = max(1, chunk_size - overlap)
        total = len(text)
        for i in range(0, total, step):
            start = i
            end = min(i + chunk_size, total)
            self._add_chunk(file_path, offset + start, offset + end, text[start:end])
            if end >= total:
                break

    def chunk_code_files(self, content: str, file_path: str) -> None:
        if not content.strip():
            return

        if len(content) <= self.max_chunk_size:
            self._add_chunk(file_path, 0, len(content), content)
        else:
            self._sliding_window(content, 0, file_path, chunk_size=1800, overlap=500)

    def chunk_doc_files(self, content: str, file_path: str) -> None:
        if not content.strip():
            return

        if len(content) <= self.max_chunk_size:
            self._add_chunk(file_path, 0, len(content), content)
        else:
            # Optimized for private docs: larger 1800 size with 500 overlap
            self._sliding_window(content, 0, file_path, chunk_size=1800, overlap=500)

    def process_document(self, target_dir: str) -> None:
        target_path = Path(target_dir)
        if not target_path.exists():
            print(f"Warning: Target path {target_dir} does not exist.")
            return

        for file_path in sorted(target_path.rglob("*")):
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.lower()
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue

            rel_path = str(file_path)

            if suffix in {".md", ".txt"}:
                self.chunk_doc_files(content, rel_path)
            elif suffix == ".py":
                self.chunk_code_files(content, rel_path)