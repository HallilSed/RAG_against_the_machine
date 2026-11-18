from pathlib import Path
from pydantic import BaseModel


class MinimalSource(BaseModel):
    file_path: str
    first_character_index: int
    last_character_index: int


class ChunkResult(MinimalSource):
    content: str


class Chunker:
    def __init__(self, max_chunk_size: int = 2000, separators: list[str] | None = None) -> None:
        self.max_chunk_size = max_chunk_size
        # Priority structural separators: paragraphs -> lines -> spaces
        self.separators = separators or ["\n\n", "\n", " "]
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

    def _recursive_split(
        self, text: str, offset: int, file_path: str, separators: list[str]
    ) -> None:
        """Recursively splits text by structural boundaries while tracking exact character offsets."""
        if len(text) <= self.max_chunk_size:
            self._add_chunk(file_path, offset, offset + len(text), text)
            return

        if not separators:
            # Hard fallback chunking if no structural separators are left
            for i in range(0, len(text), self.max_chunk_size):
                piece = text[i : i + self.max_chunk_size]
                self._add_chunk(file_path, offset + i, offset + i + len(piece), piece)
            return

        sep = separators[0]
        next_seps = separators[1:]

        if sep not in text:
            self._recursive_split(text, offset, file_path, next_seps)
            return

        parts = text.split(sep)
        buffer = ""
        buf_start = offset
        curr_offset = offset

        for i, part in enumerate(parts):
            piece = part if i == 0 else sep + part

            if len(buffer) + len(piece) <= self.max_chunk_size:
                buffer += piece
            else:
                if buffer:
                    self._recursive_split(buffer, buf_start, file_path, next_seps)
                buffer = piece
                buf_start = curr_offset

            curr_offset += len(piece)

        if buffer:
            self._recursive_split(buffer, buf_start, file_path, next_seps)

    def chunk_code_files(self, content: str, file_path: str) -> None:
        """Applies structural recursive splitting to code files."""
        if not content.strip():
            return
        self._recursive_split(content, 0, file_path, self.separators)

    def chunk_doc_files(self, content: str, file_path: str) -> None:
        """Applies structural recursive splitting to documentation files."""
        if not content.strip():
            return
        self._recursive_split(content, 0, file_path, self.separators)

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


# Public
# ./data/raw/moulinette/moulinette evaluate_student_search_results \                                                                                                         
#   data/output/search_results/UnansweredQuestions/dataset_code_public.json \
#   data/raw/datasets_public/public/AnsweredQuestions/dataset_code_public.json \
#   --k 10 \
#   --max_context_length 2000

# Private
# ./data/raw/moulinette/moulinette evaluate_student_search_results \
#   data/output/search_results/UnansweredQuestions/dataset_docs_private.json \
#   data/raw/dataset_private/private/AnsweredQuestions/dataset_docs_private.json \
#   --k 10 --max_context_length 2000