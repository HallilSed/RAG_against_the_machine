uv run python -m src.index search_dataset \
  --dataset_path data/raw/dataset_private/private/AnsweredQuestions/dataset_docs_private.json \
  --k 10 \
  --save_directory data/processed/search_treesitter_dataset_docs_private.json


uv run python -m src.index search_dataset \
  --dataset_path data/raw/dataset_private/private/AnsweredQuestions/dataset_code_private.json \
  --k 10 \
  --save_directory data/processed/search_treesitter_dataset_code_private.json