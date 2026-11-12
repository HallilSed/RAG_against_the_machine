from pathlib import Path
from pydantic import BaseModel

class MinimalSource(BaseModel):

    file_path: str
    first_character_index: int
    last_character_index: int

class ChunkResult(MinimalSource):

    content: str


class Chunker:
    def __init__(self, separator: list[str] | None = None, max_chunk_size: int = 2000) -> None:
        self.sep = separator or ["\n\n", "\n", " ", ""]
        self.max_chunk_size = max_chunk_size
    
    def chunk_document(self, content: str, file_path: str) -> list[ChunkResult]:
        chunks: list[ChunkResult] = []
        self._split_text(content, 0, file_path, self.sep, chunks)
        return chunks

    def _split_text(self, text: str, start_offset: int, file_path: str, separators: list[str], chunks: list[ChunkResult]) -> None:
        if not text:
            return

        if len(text) <= self.max_chunk_size or not separators:
            if len(text) > self.max_chunk_size:
                for i in range(0, len(text), self.max_chunk_size):
                    part = text[i : i + self.max_chunk_size]
                    if part.strip():
                        chunks.append(
                            ChunkResult(
                                file_path=file_path,
                                first_character_index=start_offset + i,
                                last_character_index=start_offset + i + len(part),
                                content=part
                            )
                        )
                return

            left_trim = len(text) - len(text.lstrip())
            right_trim = len(text) - len(text.rstrip())
            trimmed = text.strip()
            
            if trimmed:
                chunks.append(
                    ChunkResult(
                        file_path=file_path,
                        first_character_index=start_offset + left_trim,
                        last_character_index=start_offset + len(text) - right_trim,
                        content=trimmed
                    )
                )
            return

        sep = separators[0]
        next_seps = separators[1:]
        splits = text.split(sep)
        
        current_block = ""
        block_start = start_offset
        offset = start_offset

        for i, part in enumerate(splits):
            has_sep = i < len(splits) - 1
            segment = part + (sep if has_sep else "")

            if len(segment) > self.max_chunk_size:
                if current_block:
                    self._split_text(current_block, block_start, file_path, next_seps, chunks)
                    current_block = ""
                self._split_text(segment, offset, file_path, next_seps, chunks)
                offset += len(segment)
                block_start = offset
                continue

            if current_block and len(current_block) + len(segment) > self.max_chunk_size:
                self._split_text(current_block, block_start, file_path, next_seps, chunks)
                current_block = segment
                block_start = offset
            else:
                if not current_block:
                    block_start = offset
                current_block += segment

            offset += len(segment)

        if current_block:
            self._split_text(current_block, block_start, file_path, next_seps, chunks)
            

class ChunkerPY(Chunker):

    def __init__(self, separator: list[str] | None = None, max_chunk_size: int = 2000):
        default_sep = separator or ["\nclass ", "\ndef ", "\n\n", "\n", " ", ""]
        super().__init__(default_sep, max_chunk_size)
        self.sep = default_sep


    def process_py_documents(self, files_path: str) -> list[ChunkResult]:

        path = Path(files_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {files_path}")
        
        all_chunks = []
        for file in path.rglob("*.py"):
            file_content = file.read_text(encoding="utf-8")
            file_chunks = self.chunk_document(content=file_content, file_path=file.as_posix())
            all_chunks.extend(file_chunks)

        return all_chunks

# class ChunkerMd(Chunker):
    
#     def __init__(self, separator = None, max_chunk_size = 2000):
#         super().__init__(separator, max_chunk_size)
#         self.sep = separator


#     def process_md_content(self, files_path: str) -> list[ChunkResult]:
        
#         path = Path(files_path)
        
#         if not path.exists():
#             raise FileNotFoundError(f"File not found: {files_path}")
        
#         all_chunks = []
#         for i in path.rglob("*.md"):
#             file_content = i.read_text(encoding="utf-8")
#             file_chunks = self.chunk_document(content=file_content, file_path=str(i))
#             all_chunks.extend(file_chunks)
        
#         return all_chunks


class ChunkerTXT(Chunker):
    
    def __init__(self, separator: list[str] | None = None, max_chunk_size: int = 2000):
        default_sep = separator or ["\n# ", "\n## ", "\n### ", "\n\n", "\n", " ", ""]
        super().__init__(default_sep, max_chunk_size)
        self.sep = default_sep
    
    def process_txt_content(self, files_path: str) -> list[ChunkResult]:

        path = Path(files_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {files_path}")

        all_chunks = []
        for file in path.rglob("*"):
            if file.suffix.lower() in [".md", ".txt"]:
                file_content = file.read_text(encoding="utf-8")
                file_chunks = self.chunk_document(content=file_content, file_path=file.as_posix())
                all_chunks.extend(file_chunks)

        return all_chunks