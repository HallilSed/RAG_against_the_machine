from pathlib import Path
from pydantic import BaseModel

class ChunkeResult(BaseModel):
    
    file_path: str
    first_char_idx: int
    last_char_idx: int
    content: str


class Chunker:
    
    def __init__(self, separator: list[str] | None=None, max_chunk_size: int=2000) -> None:
        
        self.sep = separator
        self.max_chunk_size = max_chunk_size
    
    
    def chunk_document(self, content: str, file_path: str) -> list[ChunkeResult]:
        
        chunks: list[ChunkeResult] = []
        
        prim_sep = "\n\n"
        
        paragraphs = content.split(prim_sep)
        current_block = ""
        current_start_idx = 0
        offset = 0
        
        for i, para in enumerate(paragraphs):
            has_sep = i < len(paragraphs) - 1
            sep_str = prim_sep if has_sep else ""
            para_with_sep = para + sep_str
            
            if (
                current_block and len(current_block) + len(para_with_sep) > self.max_chunk_size
            ):
                chunks.append(
                    ChunkeResult(
                        file_path=file_path,
                        first_char_idx=current_start_idx,
                        last_char_idx=current_start_idx + len(current_block)
                    )
                )
                current_block = para_with_sep
                current_start_idx = offset
            else:
                if not current_block:
                    current_start_idx = offset
                current_block += para_with_sep
            
            offset += len(para_with_sep)
        
        if not current_block:
            chunks.append(
                ChunkeResult(
                    file_path=file_path,
                    first_char_idx=current_start_idx,
                    last_char_idx=current_start_idx + len(current_block),
                    content=current_block,
                )
            )
        
        return chunks
            

class ChunkerPY(Chunker):

    def __init__(self, separator = None, max_chunk_size = 2000):
        super().__init__(separator, max_chunk_size)
        self.sep = separator


    def process_py_documents(self, files_path: str) -> list[ChunkeResult]:

        path = Path(files_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {files_path}")
        
        for i in path.rglob("*.py"):
            content = i.read_text(encoding="utf-8")
        return self.chunk_document(content=content, files_path=str(files_path))

class ChunkerMd(Chunker):
    
    def __init__(self, separator = None, max_chunk_size = 2000):
        super().__init__(separator, max_chunk_size)
        self.sep = separator


    def process_md_content(self, files_path: str) -> list[ChunkeResult]:
        
        path = Path(files_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not fount: {files_path}")
        
        for i in path.rglob("*.md"):
            content = i.read_text(encoding="utf-8")
        return self.chunk_document(content=content, files_path=str(files_path))