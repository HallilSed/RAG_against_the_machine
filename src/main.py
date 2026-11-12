from src.chunker import ChunkerPY, ChunkerTXT, ChunkResult
from pathlib import Path
import json

def build_and_save_index(corpus_dir: str, output_dir: str, max_chunk_size: int) -> list[ChunkResult]:
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    py_chunker = ChunkerPY(max_chunk_size=max_chunk_size)
    text_chunker = ChunkerTXT(max_chunk_size=max_chunk_size)
    
    py_chunks = py_chunker.process_py_documents(corpus_dir)
    text_chunks = text_chunker.process_txt_content(corpus_dir)
    
    all_chunks: list[ChunkResult] = py_chunks + text_chunks
    
    chunks_file = output_path / "chunks.json"
    
    chunks_data = [chunk.model_dump() for chunk in all_chunks]
    
    with chunks_file.open("w", encoding="utf-8") as f:
        json.dump(chunks_data, f, indent=2, ensure_ascii=False)
    
    print(f"Ingestion complete! Indexed {len(all_chunks)} chunks under {output_dir}")
    
    return all_chunks
    

if __name__ == "__main__":
    
    file_target = "data/raw/vllm-0.10.1"
    output_dir = "data/processed/"
    build_and_save_index(file_target, output_dir, 2000)
    
    # py_file = Path("py.log")
    # txt_file = Path("txt.log")
    
    # py_chunker = ChunkerPY()
    # text_chunker = ChunkerTXT()
    
    # try:
    #     result_py = py_chunker.process_py_documents(files_path=file_target)
        
    #     with py_file.open("w", encoding="utf-8") as f:
    #         f.write(f"Total chunks: {len(result_py)}\n\n")
    #         for idx, item in enumerate(result_py, 1):
    #             f.write(f"Chunk #{idx}\n")
    #             f.write(f"Path : {item.file_path}\n")
    #             f.write(f"[{item.first_char_idx}:{item.last_char_idx}]\n")
    #             f.write(f"Text: {item.content}\n")
    #             f.write("-" * 40 + "\n")

    #     # result_md = md_chunker.process_md_content(files_path=file_target)

    #     # with md_file.open("w", encoding="utf-8") as f:
    #     #     f.write(f"Total chunks: {len(result_md)}\n\n")
    #     #     for idx, item in enumerate(result_md, 1):
    #     #         f.write(f"Chunk #{idx}\n")
    #     #         f.write(f"Path : {item.file_path}\n")
    #     #         f.write(f"[{item.first_char_idx}:{item.last_char_idx}]\n")
    #     #         f.write(f"Text: {item.content}\n")
    #     #         f.write("-" * 40 + "\n")
        
    #     result_txt = text_chunker.process_txt_content(files_path=file_target)
        
    #     with txt_file.open("w", encoding="utf-8") as f:
    #         f.write(f"Total chunks: {len(result_txt)}\n\n")
    #         for idx, item in enumerate(result_txt, 1):
    #             f.write(f"Chunk #{idx}\n")
    #             f.write(f"Path: {item.file_path}\n")
    #             f.write(f"[{item.first_char_idx}:{item.last_char_idx}]\n")
    #             f.write(f"Text: {item.content}\n")
    #             f.write("-" * 40 + "\n")
        
    # except Exception as e:
    #     print(f"Error: {e}")
