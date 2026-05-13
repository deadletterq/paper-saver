"""Outbound port: render an :class:`Article` to a PDF file."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from paper_saver.domain.models import Article


class PdfRenderer(Protocol):
    """Renders an :class:`Article` as a PDF on disk."""

    def render(self, article: Article) -> Path:
        """Render *article* and return the path to the PDF file.

        The caller owns the file and is responsible for deleting it.
        """
        ...
