"""Invariants of the :class:`Article` domain model."""

from __future__ import annotations

import dataclasses

import pytest

from paper_saver.domain.models import Article


def test_articles_are_value_objects_equal_by_field() -> None:
    a = Article(title="X", content_html="<p>c</p>", source_url="https://u.test")
    b = Article(title="X", content_html="<p>c</p>", source_url="https://u.test")
    assert a == b


def test_articles_are_immutable() -> None:
    """Article is passed across thread boundaries (extractor → renderer via
    ``asyncio.to_thread``). Immutability prevents data-race surprises."""
    a = Article(title="X", content_html="<p>c</p>", source_url="https://u.test")
    with pytest.raises(dataclasses.FrozenInstanceError):
        a.title = "Y"  # type: ignore[misc]


def test_article_is_hashable() -> None:
    a = Article(title="X", content_html="<p>c</p>", source_url="https://u.test")
    b = Article(title="X", content_html="<p>c</p>", source_url="https://u.test")
    assert hash(a) == hash(b)
