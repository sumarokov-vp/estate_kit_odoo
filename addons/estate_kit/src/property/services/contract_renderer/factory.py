import os

from .service import ContractRendererService

# dirname(__file__)=contract_renderer; ../=services ../=property ../=src ../=<module root>
_MODULE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
_TEMPLATES_DIR = os.path.join(_MODULE_ROOT, "report_templates")


class Factory:
    @staticmethod
    def create(env) -> ContractRendererService:
        typst_bin = os.environ.get("TYPST_BIN", "typst")
        return ContractRendererService(_TEMPLATES_DIR, typst_bin)
