./data/raw/moulinette/moulinette evaluate_student_search_results data/processed/search_treesitter_dataset_docs_private.json data/raw/dataset_private/private/AnsweredQuestions/dataset_docs_private.json --k 10 --max_context_length 2000


./data/raw/moulinette/moulinette evaluate_student_search_results data/processed/search_treesitter_dataset_code_private.json data/raw/dataset_private/private/AnsweredQuestions/dataset_code_private.json --k 10 --max_context_length 2000





data/raw/vllm-0.10.1/.buildkite/nightly-benchmarks/README.md

    "indexed_text": "data/raw/vllm-0.10.1/.buildkite/nightly-benchmarks/README.md\ndata raw vllm-0 10 1  buildkite nightly-benchmarks README md\n\n# vLLM benchmark suite\n\n## Introduction\n\nThis directory contains two sets of benchmark for vllm.\n\n- Performance benchmark: benchmark vllm's performance under various workload, for **developers** to gain clarity on whether their PR improves/degrades vllm's performance\n- Nightly benchmark: compare vllm's performance against alternatives (tgi, trt-llm and lmdeploy), for **the public** to know when to choose vllm.\n\nSee [vLLM performance dashboard](https://hud.pytorch.org/benchmark/llms?repoName=vllm-project%2Fvllm) for the latest performance benchmark results and [vLLM GitHub README](https://github.com/vllm-project/vllm/blob/main/README.md) for latest nightly benchmark results.\n\n## Performance benchmark quick overview\n\n**Benchmarking Coverage**: latency, throughput and fix-qps serving on A100 (the support for FP8 benchmark on H100 is coming!) and Intel® Xeon® Processors, with different models.\n\n**Benchmarking Duration**: about 1hr.\n\n**For benchmarking developers**: please try your best to constraint the duration of benchmarking to about 1 hr so that it won't take forever to run.\n\n## Nightly benchmark quick overview\n\n**Benchmarking Coverage**: Fix-qps serving on A100 (the support for FP8 benchmark on H100 is coming!) on Llama-3 8B, 70B and Mixtral 8x7B.\n\n**Benchmarking engines**: vllm, TGI, trt-llm and lmdeploy.\n\n**Benchmarking Duration**: about 3.5hrs.\n\n## Trigger the benchmark\n\nPerformance benchmark will be triggered when:\n\n- A PR being merged into vllm.\n"
