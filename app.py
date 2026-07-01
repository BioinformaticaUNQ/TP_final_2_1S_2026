from __future__ import annotations

import argparse

import Bio
import pandas as pd
import requests
from Bio import SeqIO
import PyPDF2


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke test del proyecto: valida que las dependencias carguen bien."
    )
    parser.parse_args()

    print("Python app lista")
    print(f"pandas: {pd.__version__}")
    print(f"requests: {requests.__version__}")
    print(f"PyPDF2: {PyPDF2.__version__}")
    print(f"Biopython: {Bio.__version__}")


if __name__ == "__main__":
    main()