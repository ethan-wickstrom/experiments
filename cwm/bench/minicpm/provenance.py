"""Byte identities of the normalized oracle tapes, release and shipped adapter."""

import hashlib
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

TRAIN_SHA = "96c458b2c043df456f0db53129d51beaedfed0b5c6164f5d6a2039b87d9972fb"
HELD_SHA = "98c719f0deccac27a242ee5ad52c0ab924d15895512cb877b2632bf7017024c7"
PEFT_SHA = "3609718b30c2bdd25cf1c244d95e79d5a0125fe07a8913a215f54c37b66dfa98"
CONFIG_SHA = "7c255594321ccd784683c18dfc21c9ed26636611a0a60a8fbbbe65228829fef7"
BASE_FILES = {
    "model-00000-of-00001.safetensors": "7ab8fd86563125929be78aeec8cb3969c7ed2ead3be1ab9d3ec0a9fa69c8660d",
    "model.safetensors.index.json": "162add042e75abc3d571c4a8679523fa4f1ffc55d1fea25fc6658a19d6e957ee",
    "config.json": "6a6509b646cb3169616c5ffc3196e7ccaf9d4d6bc17b266581d241a31c217714",
    "tokenizer_config.json": "094efb3cf1ff412284cc5945fc99dff58673a912760d04483a04aa1c716f66fd",
    "tokenizer.json": "3e065a558a034185fe299917b398685c1facd0169a9eea1e629eb30c171fed81",
    "special_tokens_map.json": "82d96d7a9e6ced037f12394b7ea6a5b02e6ca87e0d11edaa8d60d9be857ce7db",
    "chat_template.jinja": "7451a05cf1e28a79d97d7c0bc951028c0b1915119bf9046acd06a0e3d931f47c",
    "generation_config.json": "92afd6424501426eddcf7e1542f013d19e5987544977b4ee7bd26359bd5fd2ab",
}


def file_hash(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


@contextmanager
def verified_base(path):
    """Give the loaders only the release bytes whose digests were checked."""
    with tempfile.TemporaryDirectory(prefix="cwm-minicpm-") as directory:
        snapshot = Path(directory)
        for name, expected in BASE_FILES.items():
            target = snapshot / name
            shutil.copyfile(Path(path) / name, target)
            if file_hash(target) != expected:
                raise ValueError(f"Base snapshot digest mismatch for {name}")
        yield snapshot
