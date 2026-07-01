from __future__ import annotations

import shutil
import subprocess


def main() -> int:
    command = shutil.which("tp-bioinfo")
    if command is None:
        print("tp-bioinfo no esta disponible en este entorno.")
        print("Instala el paquete con: pip install -e .")
        return 1

    result = subprocess.run([command, "10.1042/bj3180001"], check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())