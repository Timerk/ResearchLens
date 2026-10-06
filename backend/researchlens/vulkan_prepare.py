"""Explicitly download pinned Vulkan assets and convert original reranker weights locally."""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

from researchlens.vulkan_reranking import MODELS, RUNTIME_COMMIT, RUNTIME_TAG, file_sha256

ARCHIVE_SHA256 = "89d1308941d5a86182395a07f57286da3898a9530246e8f755c26ec71267d4a2"
SOURCE_SHA256 = "a1813cfb0556c0a9d8dd4a64838d9ce66d67b2d9ed092edcca24d1c7447f461a"


def archive(url: str, path: Path, digest: str, target: Path):
    if not path.exists():
        urllib.request.urlretrieve(url, path)
    if file_sha256(path) != digest:
        raise ValueError("Downloaded archive checksum differs; remove that archive and try again")
    with zipfile.ZipFile(path) as zipped:
        if any(
            not (target / name).resolve().is_relative_to(target.resolve())
            for name in zipped.namelist()
        ):
            raise ValueError("Invalid archive paths")
        zipped.extractall(target)


def prepare(root: Path):
    from huggingface_hub import snapshot_download

    root.mkdir(parents=True, exist_ok=True)
    asset = f"llama-{RUNTIME_TAG}-bin-win-vulkan-x64.zip"
    binary_url = f"https://github.com/ggml-org/llama.cpp/releases/download/{RUNTIME_TAG}/{asset}"
    archive(binary_url, root / asset, ARCHIVE_SHA256, root / "bin")
    archive(
        f"https://codeload.github.com/ggml-org/llama.cpp/zip/{RUNTIME_COMMIT}",
        root / "source.zip",
        SOURCE_SHA256,
        root,
    )
    source = root / f"llama.cpp-{RUNTIME_COMMIT}"
    runtime = {
        "tag": RUNTIME_TAG,
        "commit": RUNTIME_COMMIT,
        "binary_sha256": ARCHIVE_SHA256,
        "binary_url": binary_url,
        "source": str(source),
    }
    (root / "runtime.json").write_text(json.dumps(runtime, indent=2) + "\n", encoding="utf-8")
    models = {}
    for alias, (model, revision) in MODELS.items():
        print(f"Preparing pinned {alias} reranker", flush=True)
        path = snapshot_download(
            model,
            revision=revision,
            token=False,
            allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model", "README.md"],
        )
        models[alias] = {"model": model, "revision": revision, "source": path}
        output = root / f"{alias}-f16.gguf"
        # Existing conversions are reused; their actual hashes are bound in every run.
        if not output.exists():
            env = os.environ.copy()
            env["PYTHONPATH"] = str(root / "convert-deps")
            with (root / f"{alias}-conversion.log").open("w", encoding="utf-8") as log:
                process = subprocess.run(
                    [
                        sys.executable,
                        str(source / "convert_hf_to_gguf.py"),
                        path,
                        "--outfile",
                        str(output),
                        "--outtype",
                        "f16",
                    ],
                    env=env,
                    stdout=log,
                    stderr=log,
                    check=False,
                )
            if process.returncode:
                raise ValueError("Conversion failed; inspect the local conversion log")
        models[alias]["weights_sha256"] = file_sha256(output)
    (root / "models.json").write_text(json.dumps(models, indent=2) + "\n", encoding="utf-8")
    print("Pinned Vulkan assets are ready; model files are not repository artifacts", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()
    try:
        prepare(args.runtime.resolve())
    except (OSError, ValueError):
        parser.exit(
            1, "Preparation failed; check network, disk space and converter dependencies.\n"
        )


if __name__ == "__main__":
    main()
