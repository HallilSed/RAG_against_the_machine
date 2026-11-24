./data/raw/moulinette/moulinette evaluate_student_search_results \
  data/output/search_results/UnansweredQuestions/dataset_docs_public.json \
  data/raw/datasets_public/public/AnsweredQuestions/dataset_docs_public.json --k 10 --max_context_length 2000


./data/raw/moulinette/moulinette evaluate_student_search_results \
  data/output/search_results/UnansweredQuestions/dataset_code_public.json \
  data/raw/datasets_public/public/AnsweredQuestions/dataset_code_public.json --k 10 --max_context_length 2000