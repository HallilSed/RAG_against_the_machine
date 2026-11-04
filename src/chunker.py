from pathlib import Path
from pydantic import BaseModel

class ChunkResult(BaseModel):
    
    file_path: str
    first_char_idx: int
    last_char_idx: int
    content: str
    
class Chunker:
    
    def __init__(self, separator: list[str] | None=None, max_chunk_size: int=2000) -> None:
        
        self.sep = separator or ["\n\n", "\n", " ", ""]
        self.max_size = max_chunk_size

    def chunk_document(self, text: str, file_path: str)-> list[ChunkResult]:
        
        chunks: list[ChunkResult] = []
        
        prim_sep = "\n\n"
        paragraphs = text.split(prim_sep)

        current_block = ""
        current_start_idx = 0
        offset = 0

        # for i in range(0, total_len, self.max_size):
        #     start_idx = i
        #     end_idx = min(i + self.max_size, total_len)

        #     chunk_text = text[start_idx:end_idx]
            
        #     chunks.append(
        #         ChunkResult(
        #             file_path=file_path,
        #             first_char_idx=start_idx,
        #             last_char_idx=end_idx,
        #             content=chunk_text,
        #         )
        #     )
        
        for i, para, in enumerate(paragraphs):
            has_sep = i < len(paragraphs) - 1
            sep_str = prim_sep if has_sep else ""
            para_with_sep = para + sep_str
            
            if (
                current_block and len(current_block) + len(para_with_sep) > self.max_size
            ):
                chunks.append(
                    ChunkResult(
                        file_path=file_path,
                        first_char_idx=current_start_idx,
                        last_char_idx=current_start_idx + len(current_block),
                        content=current_block,
                    )
                )
                
                current_block = para_with_sep
                current_start_idx = offset
            else:
                
                if not current_block:
                    current_start_idx = offset
                current_block += para_with_sep
            
            offset += len(para_with_sep)
        
        if current_block:
            chunks.append(
                ChunkResult(
                    file_path=file_path,
                    first_char_idx=current_start_idx,
                    last_char_idx=current_start_idx + len(current_block),
                    content=current_block,
                )
            )
        

        return chunks


    def process_file(self, files_path: str) -> list[ChunkResult]:

        path = Path(files_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {files_path}")

        text = path.read_text(encoding="utf-8")
        return self.chunk_document(text=text, file_path=str(path))

    


if __name__ == "__main__":
    
    file_target = "data/raw/example.txt"
    
    chunker = Chunker(max_chunk_size=2000)
    try:

        result = chunker.process_file(file_target)
        print(f"Total chunks: {len(result)}\n\n")
        
        for idx, item in enumerate(result, 1):
            print(f"Chunk #{idx}")
            # print(f"Path : {item.file_path}")
            
            print(f"[{item.first_char_idx}:{item.last_char_idx}]")
            
            print(f"Text : {item.content}")
            print("-" * 40)
        
    except Exception as e:
        print(f"{e}")