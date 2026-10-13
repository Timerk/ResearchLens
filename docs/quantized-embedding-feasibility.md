# Quantized Qwen3-4B feasibility

GGUF Q8/Q4 through llama.cpp is a possible local-memory experiment, not an adopted
retrieval backend. This change adds no GGUF artifact, dependency or quality claim.
The measured Qwen3-4B results apply to the existing pinned CPU encoder only.

Before implementing a tier, verify that a pinned llama.cpp version can convert and
embed the exact Qwen3-Embedding-4B checkpoint. Check tokenizer behavior, the fixed
query instruction, last non-padding-token pooling, output dimensions and L2
normalization. A similarly named generative checkpoint is not a substitute.

Each quantization needs its own artifact. Re-encode all passages with the same
quantized model and runtime used for queries; do not pair GGUF query embeddings
with the current dense index. Record model/conversion/runtime hashes, quantization,
encoding settings and corpus checksum in a new validated encoding contract.

Compare Q8 and Q4 on the approved development set against the existing full tier,
using the same 12k-character context and 40 candidates. Measure peak process RSS,
startup and query latency, then re-measure all five development targets. Smaller
weight files alone do not establish available-RAM requirements or retrieval quality.
Adoption requires measured headroom and all five targets passing; held-out data,
labels and canonical text remain unchanged and outside this feasibility work.
