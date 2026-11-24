uv run python -m src.retriever search_dataset \
  --dataset_path data/raw/datasets_public/public/AnsweredQuestions/dataset_docs_public.json \
  --k 10 \
  --save_directory data/output/search_results/UnansweredQuestions/dataset_docs_public.json

uv run python -m src.retriever search_dataset \
  --dataset_path data/raw/datasets_public/public/AnsweredQuestions/dataset_code_public.json \
  --k 10 \
  --save_directory data/output/search_results/UnansweredQuestions/dataset_code_public.json