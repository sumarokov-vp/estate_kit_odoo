import json
import logging
import os
import shutil
import subprocess
import tempfile

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ContractRendererService:
    def __init__(self, templates_dir: str, typst_bin: str) -> None:
        self._templates_dir = templates_dir
        self._typst_bin = typst_bin

    @property
    def _contracts_dir(self) -> str:
        return os.path.join(self._templates_dir, "contracts")

    @property
    def _fonts_dir(self) -> str:
        return os.path.join(self._contracts_dir, "fonts")

    def render_pdf(self, typst_file: str, data: dict) -> bytes:
        template_path = os.path.join(self._contracts_dir, typst_file)
        if not os.path.isfile(template_path):
            raise UserError(f"Шаблон договора не найден: {typst_file}")

        work_dir = tempfile.mkdtemp(prefix="estate_contract_")
        try:
            return self._compile(work_dir, template_path, typst_file, data)
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    def _compile(self, work_dir: str, template_path: str, typst_file: str, data: dict) -> bytes:
        work_template = os.path.join(work_dir, typst_file)
        shutil.copyfile(template_path, work_template)
        shutil.copytree(
            os.path.join(self._contracts_dir, "lib"),
            os.path.join(work_dir, "lib"),
        )

        data_path = os.path.join(work_dir, "data.json")
        with open(data_path, "w", encoding="utf-8") as data_file:
            data_file.write(json.dumps(data, ensure_ascii=False))

        out_path = os.path.join(work_dir, "out.pdf")
        result = subprocess.run(
            [
                self._typst_bin,
                "compile",
                "--font-path",
                self._fonts_dir,
                "--input",
                "data=data.json",
                work_template,
                out_path,
            ],
            cwd=work_dir,
            capture_output=True,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace")
            _logger.error("Typst compile failed (%s): %s", result.returncode, stderr)
            raise UserError(
                "Не удалось сформировать PDF договора. "
                "Проверьте настройку движка Typst и шаблон.\n\n"
                f"{stderr}"
            )

        with open(out_path, "rb") as out_file:
            return out_file.read()
