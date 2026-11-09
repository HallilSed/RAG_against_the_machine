from chunker import ChunkerMd, ChunkerPY
from pathlib import Path

if __name__ == "__main__":
    
    file_target = "data/raw/vllm-0.10.1"
    py_file = Path("py.log")
    md_file = Path("md.log")
    
    py_chunker = ChunkerPY(separator=["\nclass ", "\ndef ", "\n\n", "\n", " ", ""])
    md_chunker = ChunkerMd(separator=["\n# ", "\n## ", "\n\n", "\n", " ", ""])
    
    try:
        
        result_py = py_chunker.process_py_documents(files_path=file_target)
        
        py_file.write_text(f"Total chunks: {len(result_py)}\n\n")
        
        for idx, item in enumerate(result_py, 1):
            py_file.write_text(f"Chunk #{idx}")
            py_file.write_text(f"Path : {item.file_path}")
            
            py_file.write_text(f"[{item.first_char_idx}:{item.last_char_idx}]")
            
            py_file.write_text(f"Text: {item.content}")
            py_file.write_text("-" * 40)



        result_md = md_chunker.process_md_content(files_path=file_target)
        md_file.write_text(f"Total chunks: {len(result_py)}\n\n")
                
        for idx, item in enumerate(result_py, 1):
            md_file.write_text(f"Chunk #{idx}")
            md_file.write_text(f"Path : {item.file_path}")
            
            md_file.write_text(f"[{item.first_char_idx}:{item.last_char_idx}]")
            
            md_file.write_text(f"Text: {item.content}")
            md_file.write_text("-" * 40)
        
    except Exception as e:
        print(f"{e}")