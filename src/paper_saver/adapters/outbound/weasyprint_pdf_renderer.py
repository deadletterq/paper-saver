"""WeasyPrint adapter that renders articles to temporary PDF files."""

from __future__ import annotations

import tempfile
from importlib.resources import files
from pathlib import Path

from weasyprint import CSS, HTML

from paper_saver.adapters.outbound.pdf_document import build_document
from paper_saver.domain.models import Article


class WeasyPrintPdfRenderer:
    """Renders an :class:`Article` to a temporary PDF using WeasyPrint."""

    def __init__(self, css_path: Path | None = None) -> None:
        if css_path is None:
            css_path = Path(
                str(files("paper_saver").joinpath("assets/print_styles.css"))
            )
        self._css_path = css_path

    def render(self, article: Article) -> Path:
        document = build_document(article)
        tmp = tempfile.NamedTemporaryFile(
            prefix="paper-saver-", suffix=".pdf", delete=False
        )
        tmp.close()
        output = Path(tmp.name)
        HTML(string=document).write_pdf(
            target=str(output),
            stylesheets=[CSS(filename=str(self._css_path))],
        )
        return output
