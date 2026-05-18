"""Pure HTML template for the print PDF — no third-party dependencies.

Kept separate from the WeasyPrint binding so it can be tested on any machine
without needing pango / cairo / harfbuzz installed.
"""

from __future__ import annotations

import html

from paper_saver.domain.models import Article


def build_document(article: Article) -> str:
    """Wrap *article* in a minimal HTML document for the PDF renderer."""
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
{_render_endnotes(article.references)}</body>
</html>
"""


def _render_endnotes(references: tuple[str, ...]) -> str:
    if not references:
        return ""
    items = "".join(f"<li>{html.escape(url)}</li>" for url in references)
    return f'<section class="endnotes"><ol>{items}</ol></section>\n'
