"""Pure HTML template for the print PDF — no third-party dependencies.

Kept separate from the WeasyPrint binding so it can be tested on any machine
without needing pango / cairo / harfbuzz installed.
"""

from __future__ import annotations

import html
from collections.abc import Callable
from datetime import datetime

from paper_saver.domain.models import Article

Clock = Callable[[], datetime]


def build_document(article: Article, now: Clock = datetime.now) -> str:
    """Wrap *article* in a minimal HTML document for the PDF renderer."""
    generated = now().strftime("%Y-%m-%d %H:%M")
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
