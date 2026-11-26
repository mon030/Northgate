"""Install the pinned Windows x64 local inference files used by the demo."""
import hashlib
import os
import platform
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

RUNTIME = Path(__file__).resolve().parent / "runtime"
ENGINE_URL = "https://github.com/ggml-org/llama.cpp/releases/download/b12728/llama-b12728-bin-win-cpu-x64.zip"
ENGINE_SHA = "a8ace09d44bb10e2617268c55c3f2db0e0adeedd9c1ba722969920665a3ae698"
MODEL_URL = "https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct-GGUF/resolve/593b5a2e04c8f3e4ee880263f93e0bd2901ad47f/smollm2-360m-instruct-q8_0.gguf"
MODEL_SHA = "48ab3034d0dd401fbc721eb1df3217902fee7dab9078992d66431f09b7750201"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def download(url, path, expected):
    print(f"Downloading {path.name} …", flush=True)
    with urlopen(url, timeout=90) as response, path.open("wb") as output:
        shutil.copyfileobj(response, output)
    if digest(path) != expected:
        raise ValueError(f"Checksum mismatch for {path.name}. Run setup again.")


def install():
    if sys.platform != "win32" or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise SystemExit("The bundled local-engine configuration requires Windows x64. Rules only is available without it.")
    RUNTIME.mkdir(exist_ok=True)
    model = RUNTIME / "model.gguf"
    engine = RUNTIME / "llama"
    with tempfile.TemporaryDirectory(dir=RUNTIME, prefix="setup-") as staging:
        tmp = Path(staging)
        if not model.exists():
            download(MODEL_URL, tmp / model.name, MODEL_SHA)
            os.replace(tmp / model.name, model)
        elif digest(model) != MODEL_SHA:
            raise ValueError("Existing runtime/model.gguf differs from the pinned model. Move it aside before retrying.")
        if not engine.exists():
            archive = tmp / "llama.zip"
            download(ENGINE_URL, archive, ENGINE_SHA)
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(tmp / "llama")
            if not (tmp / "llama" / "llama-server.exe").is_file():
                raise ValueError("The verified archive does not contain the expected server.")
            os.replace(tmp / "llama", engine)
        elif not all((engine / name).is_file() for name in ("llama-server.exe", "llama-server-impl.dll", "llama.dll")):
            raise ValueError("The existing runtime/llama folder is incomplete. Move it aside before retrying.")
    print("Local model ready.")


if __name__ == "__main__":
    install()
