"""The local embedding model, shared by indexing and searching.

bge-m3 runs in this process through sentence-transformers, the way open-webui and
private-gpt load their default local models. Queries and documents use the same model and
the same input form: bge-m3 needs no query or passage prefix.
"""

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from huggingface_hub import snapshot_download, try_to_load_from_cache

from chat_bridge.config import local_data_dir
from chat_bridge.errors import LocalSetupError

if TYPE_CHECKING:
    # Importing sentence-transformers loads PyTorch, which takes several seconds. As in
    # open-webui, it is imported where the model is loaded, so commands that compute no
    # vector do not pay for it.
    from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-m3"
# Pinned to one commit of the model repository, so every machine embeds with the same weights.
MODEL_REVISION = "5617a9f61b028005a4858fdac845db406aefb181"
DIMENSIONS = 1024
# The files sentence-transformers reads for bge-m3 at the pinned commit. Only these are
# downloaded: the repository also holds an ONNX copy of the weights and two other heads.
MODEL_FILES = (
    "modules.json",
    "config_sentence_transformers.json",
    "sentence_bert_config.json",
    "1_Pooling/config.json",
    "config.json",
    "pytorch_model.bin",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "sentencepiece.bpe.model",
)
DOWNLOAD_SIZE_NOTE = "about 2.3 GB"

# A text longer than this is split, so no part is cut off by the model. private-gpt cuts
# its chunks at 0.9 of the embedding model's window, with no overlap.
CHUNK_WINDOW_SHARE = 0.9

logger = logging.getLogger(__name__)


class ModelDownloadError(LocalSetupError):
    """The embedding model is not on disk and could not be downloaded."""


def models_dir() -> str:
    return str(local_data_dir() / "models")


def is_model_downloaded() -> bool:
    """Whether every file of the pinned model is already in the local model folder."""
    return all(
        isinstance(
            try_to_load_from_cache(
                MODEL_NAME, name, cache_dir=models_dir(), revision=MODEL_REVISION
            ),
            str,
        )
        for name in MODEL_FILES
    )


def _model_folder() -> str:
    # As in open-webui, the model is downloaded once and then found in the local cache with
    # local_files_only, so later runs make no network call.
    downloaded = is_model_downloaded()
    if not downloaded:
        logger.info(
            "Downloading the embedding model %s (%s) into %s. This happens once.",
            MODEL_NAME,
            DOWNLOAD_SIZE_NOTE,
            models_dir(),
        )
    try:
        return snapshot_download(
            MODEL_NAME,
            revision=MODEL_REVISION,
            cache_dir=models_dir(),
            allow_patterns=list(MODEL_FILES),
            local_files_only=downloaded,
        )
    except OSError as error:
        # Every huggingface_hub download error is an OSError, offline mode included. Its
        # message can run over many lines; the first one names the problem.
        lines = str(error).strip().splitlines()
        raise ModelDownloadError(
            f"Could not download the embedding model {MODEL_NAME} into {models_dir()}: "
            f"{type(error).__name__}: {lines[0] if lines else ''}"
        ) from error


def load_model() -> "SentenceTransformer":
    """Load bge-m3 on the CPU, downloading the pinned files on first use.

    The model is loaded from its local folder, not by repository name. Given a name and a
    repository without safetensors weights, transformers starts a background thread that
    downloads a converted copy of the weights (another 2.3 GB) from a pull request.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(_model_folder(), device="cpu")


def _chunk_tokens(model: "SentenceTransformer") -> int:
    # bge-m3's configuration sets the window (8192 tokens); without it, the split is unknown.
    if model.max_seq_length is None:
        raise RuntimeError(f"{MODEL_NAME} has no max_seq_length in its configuration")
    return int(model.max_seq_length * CHUNK_WINDOW_SHARE)


def split_for_model(model: "SentenceTransformer", text: str) -> list[str]:
    """Split a text into parts the model reads in full, cutting at token boundaries."""
    limit = _chunk_tokens(model)
    encoded: Any = model.tokenizer(
        text, add_special_tokens=False, return_offsets_mapping=True
    )
    offsets: list[tuple[int, int]] = encoded["offset_mapping"]
    if len(offsets) <= limit:
        return [text]
    parts: list[str] = []
    for first in range(0, len(offsets), limit):
        window = offsets[first : first + limit]
        parts.append(text[window[0][0] : window[-1][1]])
    return parts


def embed_documents(
    model: "SentenceTransformer", texts: Sequence[str]
) -> list[list[float]]:
    """Embed many texts in one batched call. Vectors come back normalized."""
    # A file can hold only tables, which are not embedded, so the list can be empty.
    if not texts:
        return []
    vectors: Any = model.encode_document(
        list(texts), normalize_embeddings=True, convert_to_numpy=True
    )
    return [vector.tolist() for vector in vectors]


def embed_query(model: "SentenceTransformer", text: str) -> list[float]:
    vector: Any = model.encode_query(
        text, normalize_embeddings=True, convert_to_numpy=True
    )
    result: list[float] = vector.tolist()
    return result
