from src.chunker import Chunker
from pathlib import Path
import json

if __name__ == "__main__":
    file_target = "data/raw/vllm-0.10.1"
    output_dir = "data/processed/"

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    code_separator = ["\nclass ", "\ndef ", "\n\n", "\n", " "]
    docs_fixed_size = 2000

    chunker = Chunker(separator=code_separator, max_chunk_size=docs_fixed_size)

    chunker.process_document(file_target)

    chunks_file = output_path / "chunks.json"

    chunks_data = [chunk.model_dump() for chunk in chunker.all_chunks]

    with chunks_file.open("w", encoding="utf-8") as f:
        json.dump(chunks_data, f, indent=2, ensure_ascii=False)

    print(f"Ingestion complete! Indexed {len(chunker.all_chunks)} chunks to {chunks_file}")
