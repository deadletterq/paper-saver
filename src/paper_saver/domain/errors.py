"""Domain errors raised across port boundaries."""

from __future__ import annotations


class PaperSaverError(Exception):
    """Base class for all paper-saver domain errors."""


class FetchError(PaperSaverError):
    """The page could not be fetched."""


class ExtractionError(PaperSaverError):
    """No usable article content could be extracted from the page."""


class RenderError(PaperSaverError):
    """The article could not be rendered to PDF."""
