import json

import re
import Stemmer
from pydantic import BaseModel
from pathlib import Path

CHUNKS_FILE = Path("data/processed/chunks.json")

class MinimalSource(BaseModel):
    file_path: str
    first_character_index: int
    last_character_index: int


class Index:
    
    def __init__(self):
        pass
    
    def load_chunks(self, chunks_file: Path = CHUNKS_FILE) -> list[dict]:
        
        if not chunks_file.exists():
            raise FileNotFoundError(f"Missing {chunks_file}")
        
        chunks = json.load(chunks_file.read_text(encoding="utf-8"))
        
        if not chunks:
            raise ValueError(f"{chunks_file} file is empty")
        
        return chunks