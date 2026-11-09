from src.chunker import ChunkerMd, ChunkerPY
from pathlib import Path

if __name__ == "__main__":
    
    file_target = "data/raw/vllm-0.10.1"
    py_file = Path("py.log")
    md_file = Path("md.log")
    
    py_chunker = ChunkerPY(separator=["\nclass ", "\ndef ", "\n\n", "\n", " ", ""])
    md_chunker = ChunkerMd(separator=["\n# ", "\n## ", "\n\n", "\n", " ", ""])
    
    try:
        result_py = py_chunker.process_py_documents(files_path=file_target)
        
        with py_file.open("w", encoding="utf-8") as f:
            f.write(f"Total chunks: {len(result_py)}\n\n")
            for idx, item in enumerate(result_py, 1):
                f.write(f"Chunk #{idx}\n")
                f.write(f"Path : {item.file_path}\n")
                f.write(f"[{item.first_char_idx}:{item.last_char_idx}]\n")
                f.write(f"Text: {item.content}\n")
                f.write("-" * 40 + "\n")

        result_md = md_chunker.process_md_content(files_path=file_target)

        with md_file.open("w", encoding="utf-8") as f:
            f.write(f"Total chunks: {len(result_md)}\n\n")
            for idx, item in enumerate(result_md, 1):
                f.write(f"Chunk #{idx}\n")
                f.write(f"Path : {item.file_path}\n")
                f.write(f"[{item.first_char_idx}:{item.last_char_idx}]\n")
                f.write(f"Text: {item.content}\n")
                f.write("-" * 40 + "\n")
        
    except Exception as e:
        print(f"Error: {e}")