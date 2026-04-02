"""Dev deploy: calls shared restart script from estate_kit/dev/."""

import subprocess
import sys
from pathlib import Path

RED = "\033[0;31m"
NC = "\033[0m"

dev_dir = Path(__file__).resolve().parents[5] / "dev"
script = dev_dir / "restart-odoo.fish"

try:
    subprocess.run(["fish", str(script)], check=True)  # noqa: S603, S607
except subprocess.CalledProcessError as e:
    print(f"{RED}Deploy failed with exit code {e.returncode}{NC}", flush=True)  # noqa: T201
    sys.exit(e.returncode)
