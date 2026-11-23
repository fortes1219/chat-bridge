"""The local embedding model, shared by indexing and searching.

bge-m3 runs in this process through sentence-transformers, the way open-webui and
private-gpt load their default local models. Queries and documents use the same model and
the same input form: bge-m3 needs no query or passage prefix.
"""

import functools
import logging
import os
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from huggingface_hub import snapshot_download, try_to_load_from_cache

from chat_bridge.config import local_data_dir
from chat_bridge.errors import LocalSetupError

if TYPE_CHECKING:
    # Importing sentence-transformers loads PyTorch, which takes several seconds. As in
    # open-webui, it is imported where the model is loaded, so commands that compute no
    # vector do not pay for it. The passage splitter is imported the same way.
    from langchain_text_splitters import TextSplitter
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
HUB_CACHE_ENV = "HF_HUB_CACHE"

# A passage holds at most this many tokens of text. bge-m3 reads up to 8,192 tokens, but one
# vector for a long text stands for too many things at once to be found by any one of them.
PASSAGE_TOKEN_LIMIT = 512
# Where a passage may end, tried in this order. Chinese has no spaces between words, so without
# its full stops and commas a cut could fall in the middle of a word.
PASSAGE_SEPARATORS = (
    "\n\n",
    "\n",
    " ",
    ".",
    ",",
    "\u200b",  # zero-width space
    "\uff0c",  # fullwidth comma
    "\u3001",  # ideographic comma
    "\uff0e",  # fullwidth full stop
    "\u3002",  # ideographic full stop
    "",
)

logger = logging.getLogger(__name__)


class ModelDownloadError(LocalSetupError):
    """The embedding model is not on disk and could not be downloaded."""


def models_dir() -> str:
    """The Hugging Face cache folder that holds the model.

    HF_HUB_CACHE, huggingface_hub's own setting, picks the folder when it is set, so a
    model already downloaded there is not downloaded again, as open-webui reads
    SENTENCE_TRANSFORMERS_HOME. Otherwise the model stays with the app's other data.
    """
    return os.environ.get(HUB_CACHE_ENV) or str(local_data_dir() / "models")


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


@functools.cache
def load_model() -> "SentenceTransformer":
    """Load bge-m3 on the CPU, downloading the pinned files on first use.

    The model is loaded from its local folder, not by repository name. Given a name and a
    repository without safetensors weights, transformers starts a background thread that
    downloads a converted copy of the weights (another 2.3 GB) from a pull request.

    A process loads it once, as open-webui keeps its embedding function for the life of
    the app; the pinned revision makes every load the same model.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(_model_folder(), device="cpu")


@functools.cache
def _passage_splitter(model: "SentenceTransformer") -> "TextSplitter":
    # Length is counted with the embedding model's own tokenizer, because the limit is on what
    # that model reads.
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    return RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
        model.tokenizer,
        chunk_size=PASSAGE_TOKEN_LIMIT,
        chunk_overlap=0,
        separators=list(PASSAGE_SEPARATORS),
    )


def split_for_model(model: "SentenceTransformer", text: str) -> list[str]:
    """Split a text into passages of at most PASSAGE_TOKEN_LIMIT tokens, at natural breaks.

    A text that already fits is returned as it is, so short sections are stored unchanged.
    """
    if len(model.tokenizer.tokenize(text)) <= PASSAGE_TOKEN_LIMIT:
        return [text]
    return _passage_splitter(model).split_text(text)


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
