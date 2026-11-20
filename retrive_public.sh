uv run python -m src.index search_dataset \
  --dataset_path data/raw/datasets_public/public/AnsweredQuestions/dataset_docs_public.json \
  --k 10 \
  --save_directory data/processed/search_treesitter_dataset_docs_public.json

uv run python -m src.index search_dataset \
  --dataset_path data/raw/datasets_public/public/AnsweredQuestions/dataset_code_public.json \
  --k 10 \
  --save_directory data/processed/search_treesitter_dataset_code_public.json