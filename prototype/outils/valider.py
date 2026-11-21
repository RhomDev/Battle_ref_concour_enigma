"""Ancien point d’entrée du validateur du catalogue."""

from pathlib import Path
from runpy import run_path


if __name__ == "__main__":
    run_path(str(Path(__file__).resolve().parents[2] / "data/valider.py"), run_name="__main__")
