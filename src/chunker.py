from pathlib import Path
import re
from pydantic import BaseModel


class MinimalSource(BaseModel):
    file_path: str
    first_character_index: int
    last_character_index: int


class ChunkResult(MinimalSource):
    content: str
    indexed_text: str


class Chunker:
    def __init__(self, max_chunk_size: int = 1500) -> None:
        self.max_chunk_size = max_chunk_size
        self.all_chunks: list[ChunkResult] = []

    def _add_chunk(self, file_path: str, start: int, end: int, content: str, context_header: str = "") -> None:
        clean_content = content.strip()
        if not clean_content:
            return

        # Build search-optimized text for BM25 (Header + Content)
        path_words = file_path.replace("/", " ").replace("_", " ").replace(".", " ")
        indexed_text = f"{file_path}\n{path_words}\n{context_header}\n{content}"

        self.all_chunks.append(
            ChunkResult(
                file_path=file_path,
                first_character_index=start,
                last_character_index=end,
                content=content,
                indexed_text=indexed_text,
            )
        )

    def chunk_doc_files(self, content: str, file_path: str) -> None:
        """Fixed line-snapping window for .md / .txt files."""
        total = len(content)
        pos = 0

        while pos < total:
            if total - pos <= self.max_chunk_size:
                self._add_chunk(file_path, pos, total, content[pos:total])
                break

            hard_end = pos + self.max_chunk_size
            newline_idx = content.rfind("\n", pos + (self.max_chunk_size // 2), hard_end)
            end = newline_idx + 1 if newline_idx > pos else hard_end

            self._add_chunk(file_path, pos, end, content[pos:end])
            pos = end

    def chunk_code_files(self, content: str, file_path: str) -> None:
        """
        Line-by-line structural chunker for Python files.
        Keeps function and class definitions intact while tracking exact character offsets.
        """
        lines = content.splitlines(keepends=True)
        if not lines:
            return

        current_chunk = ""
        chunk_start_idx = 0
        curr_offset = 0
        active_class = ""
        active_def = ""

        for line in lines:
            # Simple line inspection for definition context
            stripped = line.strip()
            if stripped.startswith("class "):
                match = re.search(r"class\s+([a-zA-Z0-9_]+)", stripped)
                if match:
                    active_class = match.group(1)
            elif stripped.startswith("def ") or stripped.startswith("async def "):
                match = re.search(r"(?:async\s+)?def\s+([a-zA-Z0-9_]+)", stripped)
                if match:
                    active_def = match.group(1)

            # Check if adding this line exceeds target size
            if len(current_chunk) + len(line) > self.max_chunk_size and current_chunk:
                context_hdr = f"# Class: {active_class} | Def: {active_def}"
                self._add_chunk(
                    file_path,
                    chunk_start_idx,
                    curr_offset,
                    current_chunk,
                    context_header=context_hdr,
                )
                current_chunk = line
                chunk_start_idx = curr_offset
            else:
                current_chunk += line

            curr_offset += len(line)

        if current_chunk:
            context_hdr = f"# Class: {active_class} | Def: {active_def}"
            self._add_chunk(
                file_path,
                chunk_start_idx,
                curr_offset,
                current_chunk,
                context_header=context_hdr,
            )

    def process_document(self, target_dir: str) -> None:
        target_path = Path(target_dir)
        if not target_path.exists():
            print(f"Warning: Target path {target_dir} does not exist.")
            return

        files = [target_path] if target_path.is_file() else sorted(target_path.rglob("*"))
        for file_path in files:
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.lower()
            if suffix not in {".py", ".md", ".txt"}:
                continue

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