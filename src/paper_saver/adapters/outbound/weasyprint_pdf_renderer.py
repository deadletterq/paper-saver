"""WeasyPrint adapter that renders articles to temporary PDF files."""

from __future__ import annotations

import html
import tempfile
from datetime import datetime
from importlib.resources import files
from pathlib import Path

from weasyprint import CSS, HTML

from paper_saver.domain.models import Article


def _build_html(article: Article) -> str:
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(article.title)}</title>
</head>
<body>
<h1>{html.escape(article.title)}</h1>
<p class="source-url">{html.escape(article.source_url)}</p>
<main>{article.content_html}</main>
<div class="footer">Generated {generated}</div>
</body>
</html>
"""


class WeasyPrintPdfRenderer:
    """Renders an :class:`Article` to a temporary PDF using WeasyPrint."""

    def __init__(self, css_path: Path | None = None) -> None:
        if css_path is None:
            css_path = Path(
                str(files("paper_saver").joinpath("assets/print_styles.css"))
            )
        self._css_path = css_path

    def render(self, article: Article) -> Path:
        document = _build_html(article)
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
