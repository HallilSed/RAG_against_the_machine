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

        total_len = len(text)
        start_idx = 0

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
        
        while start_idx < total_len:
            
            if total_len - start_idx <= self.max_size:
                end_idx = total_len
            else:
                max_end = start_idx + self.max_size
                end_idx = max_end
            
            for sep in ["\n\n", "\n", " "]:
                sep_pos = text.rfind(sep, start_idx, max_end)
                if sep_pos != -1 and sep_pos > start_idx:
                    end_idx = sep_pos + len(sep)
                    break
            
            chunk_text = text[start_idx:end_idx]
            
            
            chunks.append(
                ChunkResult(
                    file_path=file_path,
                    first_char_idx=start_idx,
                    last_char_idx=end_idx,
                    content=chunk_text,
                )
            )
            
            start_idx = end_idx

        return chunks


    def process_file(self, files_path: str) -> list[ChunkResult]:

        path = Path(files_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {files_path}")

        text = path.read_text(encoding="utf-8")
        return self.chunk_document(text=text, file_path=str(path))
        
    


if __name__ == "__main__":
    
    file_target = "../data/raw/example.txt"
    
    chunker = Chunker(max_chunk_size=200)
    try:
        
        result = chunker.process_file(file_target)
        print(f"Total chunks: {len(result)}\n\n")
        
        for idx, item in enumerate(result, 1):
            print(f"Chunk #{idx}")
            # print(f"Path : {item.file_path}")
            
            print(f"[{item.first_char_idx}:{item.last_char_idx}]")
            
            print(f"Text : {repr(item.content)}")
            print("-" * 40)
        
    except Exception as e:
        print(f"{e}")