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
    
    def load_and_filter_chunks(self, chunks_file: Path = CHUNKS_FILE) -> list[dict]:
        
        if not chunks_file.exists():
            raise FileNotFoundError(f"Missing {chunks_file}")
        
        chunks = json.load(chunks_file.read_text(encoding="utf-8"))
        
        if not chunks:
            raise ValueError(f"{chunks_file} file is empty")
        
    
    def build_tokenizer(self, text: str) -> list[str]:
        
        expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
        exp_prev = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", expanded)
        
        parts = re.findall(r"[a-zA-Z0-9]+", exp_prev.lower())
        snake = re.findall(r"[a-zA-Z0-9]+(?:_[a-zA-Z0-9]+)+", text.lower())
        
        return parts + snake
    
    