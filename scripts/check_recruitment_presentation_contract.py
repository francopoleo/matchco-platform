"""Verifica se a apresentação comercial corresponde ao contrato canônico."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "matchco/docs/atual/CONTRATO_RECRUTAMENTO.md"
PRESENTATION = ROOT / "matchco/docs/help/html/03_RECRUITMENT_APRESENTACAO_VENDAS.html"


def main() -> int:
    contract = CONTRACT.read_bytes()
    presentation = PRESENTATION.read_text(encoding="utf-8")
    version_match = re.search(r"Versão de revisão:\s*([0-9]+\.[0-9]+\.[0-9]+)", contract.decode("utf-8"))
    html_version = re.search(r'data-contract-version="([^"]+)"', presentation)
    html_sha = re.search(r'data-contract-sha256="([0-9a-f]+)"', presentation)
    if not version_match or not html_version or not html_sha:
        print("Contrato ou apresentação sem metadados de vínculo.", file=sys.stderr)
        return 1
    expected_version = version_match.group(1)
    expected_sha = hashlib.sha256(contract).hexdigest()
    if html_version.group(1) != expected_version:
        print(f"Versão divergente: contrato {expected_version}, apresentação {html_version.group(1)}.", file=sys.stderr)
        return 1
    if html_sha.group(1) != expected_sha:
        print("A apresentação está desatualizada em relação ao contrato.", file=sys.stderr)
        print(f"Atualize data-contract-sha256 para {expected_sha} após revisar os slides.", file=sys.stderr)
        return 1
    print(f"Apresentação vinculada ao contrato {expected_version} ({expected_sha[:12]}…).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
