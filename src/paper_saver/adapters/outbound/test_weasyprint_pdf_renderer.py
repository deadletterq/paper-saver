"""Smoke test for the WeasyPrint adapter against the real backend.

WeasyPrint requires native libraries (pango, cairo, harfbuzz). This test
is skipped automatically on machines where they are unavailable so the
test suite stays runnable in any dev environment.
"""

from __future__ import annotations

from pathlib import Path

import pytest

try:
    import weasyprint  # noqa: F401
except (ImportError, OSError) as exc:
    pytest.skip(
        f"weasyprint native libraries unavailable: {exc}",
        allow_module_level=True,
    )

from paper_saver.adapters.outbound.weasyprint_pdf_renderer import (  # noqa: E402
    WeasyPrintPdfRenderer,
)
from paper_saver.domain.models import Article  # noqa: E402


def test_render_produces_a_real_pdf_file() -> None:
    article = Article(
        title="Hello World",
        content_html="<p>Some real content.</p>",
        source_url="https://e.test/post",
    )

    pdf = WeasyPrintPdfRenderer().render(article)

    try:
        assert pdf.exists()
        assert pdf.suffix == ".pdf"
        # PDF file signature.
        assert pdf.read_bytes()[:4] == b"%PDF"
    finally:
        pdf.unlink(missing_ok=True)


def test_render_uses_custom_css_when_provided(tmp_path: Path) -> None:
    """The renderer's css_path argument is the seam used by tests and the
    composition root. A working renderer must accept any readable CSS file."""
    minimal_css = tmp_path / "min.css"
    minimal_css.write_text("body { font-size: 9pt; }")

    article = Article(
        title="t", content_html="<p>c</p>", source_url="https://e.test"
    )

    pdf = WeasyPrintPdfRenderer(css_path=minimal_css).render(article)
    try:
        assert pdf.read_bytes()[:4] == b"%PDF"
    finally:
        pdf.unlink(missing_ok=True)
