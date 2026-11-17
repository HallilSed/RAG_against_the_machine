from pathlib import Path
from pydantic import BaseModel


class MinimalSource(BaseModel):
    file_path: str
    first_character_index: int
    last_character_index: int


class ChunkResult(MinimalSource):
    content: str


class Chunker:
    def __init__(
        self, separator: list[str] | None = None, max_chunk_size: int = 2000
    ) -> None:
        # Concerns .py files in future steps
        self.sep = separator

        # Fixed size budget for docs (.md and .txt)
        self.fixed_size = max_chunk_size

        self.all_chunks: list[ChunkResult] = []

    def _split_text(
            self, text: str, offset: int, separators: list[str], file_path: str
        ) -> None:
            """Recursively splits and groups text by priority separators while tracking exact character offsets."""
            if len(text) <= self.fixed_size:
                self.all_chunks.append(
                    ChunkResult(
                        file_path=file_path,
                        first_character_index=offset,
                        last_character_index=offset + len(text),
                        content=text,
                    )
                )
                return
    
            for idx, sep in enumerate(separators):
                if sep not in text:
                    continue
    
                parts = text.split(sep)
                next_seps = separators[idx + 1 :]
                buffer, buf_start, curr_offset = "", offset, offset
    
                for i, part in enumerate(parts):
                    piece = part if i == 0 else sep + part
    
                    if len(buffer) + len(piece) <= self.fixed_size:
                        buffer += piece
                    else:
                        if buffer:
                            self._split_text(buffer, buf_start, next_seps, file_path)
                        buffer, buf_start = piece, curr_offset
    
                    curr_offset += len(piece)
    
                if buffer:
                    self._split_text(buffer, buf_start, next_seps, file_path)
                return
    
            for i in range(0, len(text), self.fixed_size):
                chunk = text[i : i + self.fixed_size]
                self.all_chunks.append(
                    ChunkResult(
                        file_path=file_path,
                        first_character_index=offset + i,
                        last_character_index=offset + i + len(chunk),
                        content=chunk,
                    )
                )
    
    def chunk_code_files(self, content: str, file_path: str) -> None:
        if content:
            self._split_text(content, 0, self.sep, file_path)
            

    def chunk_doc_files(self, content: str, file_path: str) -> None:
        if not content:
            return

        total_length = len(content)
        for start_idx in range(0, total_length, self.fixed_size):
            end_idx = min(start_idx + self.fixed_size, total_length)
            chunk_text = content[start_idx:end_idx]

            chunk = ChunkResult(
                file_path=file_path,
                first_character_index=start_idx,
                last_character_index=end_idx,
                content=chunk_text,
            )
            self.all_chunks.append(chunk)

    def process_document(self, target_dir: str) -> None:
        target_path = Path(target_dir)

        if not target_path.exists():
            print(f"Warning: Target path {target_dir} does not exist.")
            return

        for file_path in sorted(target_path.rglob("*")):
            if file_path.is_file() and file_path.suffix.lower() in [".md", ".txt"]:
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    self.chunk_doc_files(content, str(file_path))
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
            elif file_path.is_file() and file_path.suffix.lower() == ".py":
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    self.chunk_code_files(content, str(file_path))
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
