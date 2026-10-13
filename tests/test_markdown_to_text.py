import pytest
from utils.markdown_to_text import markdown_to_plaintext, clean_repeated_patterns, remove_all_urls


def test_removes_links_and_urls():
    text = "Check our [website](https://example.com) and https://example.org/page."
    cleaned = markdown_to_plaintext(text)
    assert "website" in cleaned
    assert "https://" not in cleaned
    assert "http://" not in cleaned


def test_removes_markdown_formatting():
    text = "# Heading\n\n**bold** and *italic* and `code`."
    cleaned = markdown_to_plaintext(text)
    assert "Heading" in cleaned
    assert "**" not in cleaned
    assert "*italic*" not in cleaned
    assert "`code`" not in cleaned or "code" in cleaned


def test_normalizes_lists():
    text = "- item one\n- item two\n\n1. first\n2. second"
    cleaned = markdown_to_plaintext(text)
    assert "item one" in cleaned
    assert "first" in cleaned
    assert "4. " not in cleaned


def test_deduplicates_repeating_patterns():
    text = "\n".join(["Our Company"] * 5) + "\nContent"
    cleaned = clean_repeated_patterns(text)
    assert cleaned.count("Our Company") == 1
    assert "Content" in cleaned


def test_empty_input():
    assert markdown_to_plaintext("") == ""
    assert markdown_to_plaintext(None) == ""


def test_remove_all_urls_strips_markdown_links():
    text = "[label](http://foo.com) and <http://bar.com>"
    cleaned = remove_all_urls(text)
    assert "http://" not in cleaned