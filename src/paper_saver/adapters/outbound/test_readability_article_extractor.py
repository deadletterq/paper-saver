"""Behavior specification for :class:`ReadabilityArticleExtractor`.

The extractor converts noisy web HTML into a clean, print-ready article. These
tests pin the behaviors that matter for the rendered PDF: the title is
captured, the body survives, and anything that wastes paper or breaks print
layout is stripped.
"""

from __future__ import annotations

import pytest

from paper_saver.adapters.outbound.readability_article_extractor import (
    ReadabilityArticleExtractor,
)
from paper_saver.domain.errors import ExtractionError

# Readability requires a non-trivial body to consider a node "the article",
# so every fixture is padded with filler paragraphs.
_FILLER = " ".join(["lorem ipsum dolor sit amet consectetur"] * 30)


def _page(body_html: str, title: str = "Sample") -> str:
    return (
        f"<html><head><title>{title}</title></head>"
        f"<body><article>{body_html}<p>{_FILLER}</p></article></body></html>"
    )


@pytest.fixture
def extractor() -> ReadabilityArticleExtractor:
    return ReadabilityArticleExtractor()


class TestTitleAndSourceUrl:
    def test_extracts_title_from_head(
        self, extractor: ReadabilityArticleExtractor
    ) -> None:
        html = _page("<p>some body text.</p>", title="My Great Article")
        article = extractor.extract(html, "https://e.test/a")
        assert article.title == "My Great Article"

    def test_preserves_source_url_verbatim(
        self, extractor: ReadabilityArticleExtractor
    ) -> None:
        article = extractor.extract(_page("<p>body.</p>"), "https://e.test/x?q=1")
        assert article.source_url == "https://e.test/x?q=1"


class TestVisualMediaIsStripped:
    """Images and other media don't print well and waste paper. They must go."""

    @pytest.mark.parametrize(
        "tag,element",
        [
            ("img", '<img src="x.png" alt="x">'),
            ("picture", '<picture><source srcset="b.png"></picture>'),
            ("figure", '<figure><img src="z.png"></figure>'),
            ("video", '<video src="c.mp4"></video>'),
            ("iframe", '<iframe src="https://e.test/embed"></iframe>'),
            ("svg", "<svg><circle cx='0' cy='0' r='1'/></svg>"),
        ],
    )
    def test_visual_tag_is_stripped(
        self,
        extractor: ReadabilityArticleExtractor,
        tag: str,
        element: str,
    ) -> None:
        html = _page(f"<p>Before {element} after.</p>")
        article = extractor.extract(html, "https://e.test")
        assert f"<{tag}" not in article.content_html


class TestScriptsAndStylesAreStripped:
    """Scripts and styles produce visible junk in print output."""

    def test_script_blocks_are_removed(
        self, extractor: ReadabilityArticleExtractor
    ) -> None:
        html = _page("<script>alert(1)</script><p>body.</p>")
        article = extractor.extract(html, "https://e.test")
        assert "alert" not in article.content_html
        assert "<script" not in article.content_html

    def test_style_blocks_are_removed(
        self, extractor: ReadabilityArticleExtractor
    ) -> None:
        html = _page("<style>p { color: red }</style><p>body.</p>")
        article = extractor.extract(html, "https://e.test")
        assert "color: red" not in article.content_html
        assert "<style" not in article.content_html

    def test_inline_style_attributes_are_removed(
        self, extractor: ReadabilityArticleExtractor
    ) -> None:
        html = _page('<p style="color: red; font-size: 99px">body.</p>')
        article = extractor.extract(html, "https://e.test")
        assert "style=" not in article.content_html


class TestAnchorsAreUnwrapped:
    """We don't want long URLs trailing through printed text. <a> becomes
    plain text — the label survives, the href doesn't."""

    def test_anchor_tag_is_removed(
        self, extractor: ReadabilityArticleExtractor
    ) -> None:
        html = _page('<p>See <a href="https://elsewhere.test">the source</a>.</p>')
        article = extractor.extract(html, "https://e.test")
        assert "<a " not in article.content_html
        assert "</a>" not in article.content_html

    def test_anchor_text_is_preserved(
        self, extractor: ReadabilityArticleExtractor
    ) -> None:
        html = _page('<p>See <a href="https://elsewhere.test">the source</a>.</p>')
        article = extractor.extract(html, "https://e.test")
        assert "the source" in article.content_html

    def test_href_value_is_discarded(
        self, extractor: ReadabilityArticleExtractor
    ) -> None:
        html = _page('<p>See <a href="https://elsewhere.test/x?y=1">label</a>.</p>')
        article = extractor.extract(html, "https://e.test")
        assert "elsewhere.test" not in article.content_html


class TestFailureModes:
    def test_raises_when_page_yields_no_extractable_content(
        self, extractor: ReadabilityArticleExtractor
    ) -> None:
        html = (
            "<html><body><article>"
            "<script>1</script><style>x{}</style><img src='x'>"
            "</article></body></html>"
        )
        with pytest.raises(ExtractionError):
            extractor.extract(html, "https://e.test")
