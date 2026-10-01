# AMD RX 6800 inference investigation

Research date: 2026-10-02. Scope: inference and repeated retrieval evaluations on the existing Windows machine, not training. Primary sources were fetched directly. AMD pages served ROCm 7.2.1 documentation; llama.cpp source was inspected at commit `a868c3e3c56657f7e8a6231190dbbe90e7dd86c0`. Rolling documentation links can change.

The RX 6800 has practical GPU inference routes for these models. The most useful candidates are ONNX Runtime DirectML for the existing encoder models, and llama.cpp Vulkan for Qwen3 embeddings and the stronger rerankers. AMD's current official ROCm Radeon support matrices do not list this card. That excludes a supported ROCm installation, not all GPU inference.

## Local environment

The investigating parent agent observed an RX 6800 and an integrated AMD GPU, driver `32.0.21045.5002`, Python 3.13.14, and ONNX Runtime 1.30.0 with only Azure and CPU execution providers. The repository requires Python >=3.13 and Torch >=2.7, uses Transformers 5, and pins the CPU Torch package. These are local observations rather than statements from vendor documentation. GPU use therefore needs an explicit backend and adapter selection; the current CPU installation does not become GPU-enabled automatically.

The parent agent completed an isolated DirectML check in `.venv/gpu-probe`, using Python 3.13 and ONNX Runtime DirectML 1.24.4. The project's runtime and dependencies were unchanged. DXGI adapter 0 was the RX 6800, reporting 17,130,819,584 dedicated bytes; adapter 1 was the integrated GPU. The probe used exact pinned, cached MiniLM embedding and reranker ONNX assets, with no new model-weight downloads.

Each measurement used a synthetic batch of eight repeated technical-sentence inputs, three warmups and twenty timed calls. Both providers used sequential execution, disabled memory patterns and two CPU threads. Tokenization used truncation caps of 256 for embeddings and 512 for reranking. Profiling stopped before timing. The probe script is an ignored local artifact at `.venv/gpu_probe.py`.

| Cached model | Input shape | CPU median | DirectML median | Maximum absolute output difference |
| --- | --- | --- | --- | --- |
| MiniLM embedding | 8 x 194 tokens | 75.37 ms | 10.66 ms | 0.00000309944 in raw output tensors |
| MiniLM reranker | 8 x 203 tokens | 104.97 ms | 10.23 ms | 0.00000333786 in logits |

Provider profiles recorded mixed execution. Embedding warmups contained 642 DirectML and 228 CPU events; reranker warmups contained 651 DirectML and 228 CPU events. These event counts establish that the GPU participated; they are not percentages of compute or proof of complete offload. A prior short-input probe showed little gain. The table measures warm inference on these synthetic inputs, excluding model loading, and is not a corpus evaluation, proof of identical rankings, or an end-to-end latency benchmark.

## Backend options

| Route | Evidence and status | Assessment for this machine |
| --- | --- | --- |
| ROCm PyTorch on native Windows | AMD's ROCm 7.2.1 matrix lists gfx1201, gfx1200, gfx1100 and gfx1101 devices. RX 6800 / gfx1030 is absent. The page lists PyTorch 2.9 and Python 3.12. [1] | Not an officially supported route for this card. |
| ROCm under WSL | AMD's ROCm 7.2.1 WSL matrix lists selected RX 7000/9000 and workstation cards; RX 6800 is absent. [2] | Installing WSL does not solve official hardware support. |
| ROCm under native Linux | AMD's current Radeon matrix also omits RX 6800. [3] | Community packages or architecture overrides are experimental; do not make them the first path for this Windows project. |
| ONNX Runtime DirectML | Officially accepts DirectX 12 devices, with AMD support extending to GCN-era cards. [4] | Appropriate Windows GPU API for RX 6800. Exact ONNX graphs, dtypes and operator placement still need verification. |
| PyTorch DirectML | Microsoft's native Windows guide describes public-preview support for DirectX 12 GPUs. [5] Published package metadata currently provides Python 3.8-3.12 wheels and pins Torch 2.4.1. [6] | Conflicts with this repository's Python >=3.13 and Torch >=2.7 constraints. Use only in a separate environment if needed. Not the simplest integration. |
| llama.cpp Vulkan | Upstream documents Windows Vulkan builds with `GGML_VULKAN=ON`. Model conversion and serving support exist for the relevant families. [7-11] | Strong option that avoids the project's Python Torch backend constraints. Requires a compatible GGUF model, GPU offload verification and output comparison. Not yet proven on this specific machine. |

The parent agent inspected official PyPI metadata and found a Windows Python 3.13 wheel for `onnxruntime-directml` 1.24.4. [12] This is a different distribution/version from the installed ONNX Runtime 1.30.0; use an isolated environment for the initial comparison. `onnxruntime` and `onnxruntime-directml` share the Python import name, so installing both into the same environment is not a clean A/B test.

## Model-specific findings

| Model | Recommended first GPU route | Evidence and remaining work |
| --- | --- | --- |
| MiniLM embedding | ONNX Runtime DirectML | Observed GPU execution on the cached ONNX model, with close raw outputs in the local probe above. Preserve tokenizer, attention-mask pooling and normalization. Other quantized graphs still need verification. [4, 13] |
| MiniLM cross-encoder reranker | ONNX Runtime DirectML | Observed GPU execution and close logits on the cached ONNX model. Corpus rankings remain unchecked. Preserve query/passage pair tokenization and classifier scores. [4, 14] |
| BGE-M3 embedding | DirectML with a tested ONNX export, or llama.cpp Vulkan for dense vectors | llama.cpp's XLM-R conversion explicitly lists BGE-M3 as an example. BGE-M3 also supports sparse and multivector outputs; a dense GGUF path must not be described as support for all of those outputs. [10, 15] |
| Qwen3-Embedding-0.6B / 4B | llama.cpp Vulkan | Qwen publishes official GGUF repositories for both sizes and documents llama.cpp with `--embedding --pooling last`. Preserve the query instruction, last-token pooling and normalization. [8, 9] |
| BGE-reranker-v2-m3 | llama.cpp Vulkan, or DirectML after export | The llama.cpp server documentation explicitly names this model for its reranking endpoint with rank pooling. Its converter supports `XLMRobertaForSequenceClassification`. GPU execution still needs a local test. [10, 11] |
| Qwen3-Reranker-0.6B | Recent llama.cpp Vulkan with the correct reranker conversion | Current upstream conversion explicitly recognizes Qwen3 rerankers, extracts the `yes` and `no` output-head rows, sets rank pooling and writes the reranking prompt template. This is stronger evidence than merely knowing Qwen3 generation works. Pin a version containing that implementation and compare scores against the official Transformers example. [10, 16] |

## Correctness details that affect the experiment

Qwen3 reranking scores are a two-class normalization of the final-token `yes` and `no` logits, using the model's prescribed prompt. Generating text and interpreting a verbal answer is not the same scoring procedure. Current llama.cpp conversion retains the two classifier rows and supplies the prompt, but a generic old Qwen3 GGUF or old runtime may lack those changes. Verify the converted model metadata and compare pair scores, including near ties. [10, 16]

BGE-reranker-v2-m3 uses a sequence-classification score; its model card describes optional sigmoid normalization. Do not substitute vector similarity for this score. [17]

DirectML requires `execution_mode=ORT_SEQUENTIAL` and `enable_mem_pattern=False`. It does not support concurrent calls to `Run` on one session, although separate sessions can run concurrently. The adapter ID uses DXGI enumeration, and adapter zero can be the integrated GPU. Verify RX 6800 selection. The documentation recommends known tensor shapes for efficiency, so batch size and padded sequence length belong in the benchmark record. [4]

The retrieved DirectML provider page describes DirectML 1.15.2 and support through ONNX opset 20, with named exceptions. Treat that as the documented baseline rather than assuming any newer exporter output will run. Profile node placement: a successful session with the DirectML provider available can still execute some operations on CPU. [4]

Approximate weights alone need 1.2 GB for 0.6 billion parameters at 16 bits and 8 GB for 4 billion parameters at 16 bits. These are arithmetic estimates, not measured total VRAM use. Activations, attention/KV storage, batch size, sequence length and the runtime add memory. A 16 GB card is therefore a sensible target for the 0.6B models and a plausible target for a 4B embedding model with restrained batches. It does not guarantee 32K context at a useful batch size. Quantization changes both memory use and model numerics and should be evaluated as a separate variable. Model sizes and context specifications are in Qwen's cards. [8, 9, 16]

## Recommended sequence

1. The isolated cached-MiniLM DirectML probe has passed. Next compare real corpus inputs and rankings, and decide how to expose the provider explicitly in the application. CPU fallback is present and should remain visible in benchmark records.
2. Test BGE-reranker-v2-m3 and Qwen3-Reranker-0.6B through a pinned recent llama.cpp Vulkan build. They address the ranking bottleneck directly. Start with short representative pairs and small batches, then expand to the actual evaluation lengths.
3. Test Qwen3-Embedding-0.6B through its official GGUF, then 4B if embedding experiments justify it. Match the existing embedding configuration before rebuilding an index.
4. Separate model loading and first-run compilation from warm latency and throughput. Compare batch sizes and actual sequence-length distributions. Record GPU memory, numerical agreement and retrieval metrics alongside time.

The local probe establishes faster warm inference for the two tested MiniLM input shapes. It establishes no new retrieval-quality improvement or end-to-end application GPU support. The larger models need their own checks. GGUF conversion and quantization can change artifacts and precision relative to the current Transformers path; identify both in every result. Rebuild embedding indexes and their model/configuration bindings when switching embeddings unless equivalence is established explicitly.

## Primary sources

1. [AMD native Windows Radeon support matrix, ROCm 7.2.1](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/windows/windows_compatibility.html).
2. [AMD WSL Radeon support matrix, ROCm 7.2.1](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/wsl/wsl_compatibility.html).
3. [AMD native Linux Radeon support matrix, ROCm 7.2.1](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/native_linux/native_linux_compatibility.html).
4. [ONNX Runtime DirectML execution provider](https://onnxruntime.ai/docs/execution-providers/DirectML-ExecutionProvider.html).
5. [Microsoft PyTorch with DirectML on Windows](https://learn.microsoft.com/en-us/windows/ai/directml/pytorch-windows), page dated 2026-09-08 when retrieved.
6. [torch-directml package metadata](https://pypi.org/pypi/torch-directml/json), current package 0.2.5.dev240914.
7. [llama.cpp Windows Vulkan build instructions](https://github.com/ggml-org/llama.cpp/blob/a868c3e3c56657f7e8a6231190dbbe90e7dd86c0/docs/build.md#vulkan).
8. [Qwen official Qwen3-Embedding-0.6B-GGUF model card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B-GGUF).
9. [Qwen official Qwen3-Embedding-4B-GGUF model card](https://huggingface.co/Qwen/Qwen3-Embedding-4B-GGUF).
10. llama.cpp conversion implementations: [Qwen3 reranker](https://github.com/ggml-org/llama.cpp/blob/a868c3e3c56657f7e8a6231190dbbe90e7dd86c0/conversion/qwen.py), [BERT and XLM-R](https://github.com/ggml-org/llama.cpp/blob/a868c3e3c56657f7e8a6231190dbbe90e7dd86c0/conversion/bert.py), and [Qwen3 runtime model](https://github.com/ggml-org/llama.cpp/blob/a868c3e3c56657f7e8a6231190dbbe90e7dd86c0/src/models/qwen3.cpp).
11. [llama.cpp server documentation, embedding and reranking endpoints](https://github.com/ggml-org/llama.cpp/blob/a868c3e3c56657f7e8a6231190dbbe90e7dd86c0/tools/server/README.md).
12. [onnxruntime-directml package metadata](https://pypi.org/pypi/onnxruntime-directml/json).
13. [Sentence Transformers all-MiniLM-L6-v2 official model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2).
14. [Cross-encoder ms-marco-MiniLM-L6-v2 official model card](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2).
15. [BAAI BGE-M3 official model card](https://huggingface.co/BAAI/bge-m3).
16. [Qwen Qwen3-Reranker-0.6B official model card and scoring example](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B).
17. [BAAI BGE-reranker-v2-m3 official model card](https://huggingface.co/BAAI/bge-reranker-v2-m3).
