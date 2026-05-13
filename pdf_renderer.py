"""Render a cleaned article dict to a print-optimized PDF via WeasyPrint."""

from __future__ import annotations

import html
import tempfile
from datetime import datetime
from pathlib import Path

from weasyprint import CSS, HTML

CSS_FILENAME = "print_styles.css"


def _build_html(title: str, content_html: str, source_url: str) -> str:
    """Wrap the extracted body in a minimal HTML document."""
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    safe_title = html.escape(title)
    safe_source = html.escape(source_url)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{safe_title}</title>
</head>
<body>
<h1>{safe_title}</h1>
<p class="source-url">{safe_source}</p>
<main>{content_html}</main>
<div class="footer">Generated {generated}</div>
</body>
</html>
"""


def render_pdf(
    title: str,
    content_html: str,
    source_url: str,
    css_path: Path | None = None,
) -> Path:
    """Render the article to a temporary PDF file and return its path.

    The caller is responsible for deleting the file once it has been sent.
    """
    css_file = css_path or (Path(__file__).parent / CSS_FILENAME)
    document = _build_html(title, content_html, source_url)

    tmp = tempfile.NamedTemporaryFile(
        prefix="paper-saver-", suffix=".pdf", delete=False
    )
    tmp.close()
    output = Path(tmp.name)

    HTML(string=document).write_pdf(
        target=str(output),
        stylesheets=[CSS(filename=str(css_file))],
    )
    return output
