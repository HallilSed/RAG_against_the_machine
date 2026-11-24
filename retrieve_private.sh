uv run python -m src.retriever search_dataset \
  --dataset_path data/raw/dataset_private/private/AnsweredQuestions/dataset_docs_private.json \
  --k 10 \
  --save_directory data/output/search_results/UnansweredQuestions/dataset_docs_private.json


uv run python -m src.retriever search_dataset \
  --dataset_path data/raw/dataset_private/private/AnsweredQuestions/dataset_code_private.json \
  --k 10 \
  --save_directory data/output/search_results/UnansweredQuestions/dataset_code_private.json