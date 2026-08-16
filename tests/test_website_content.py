"""Tests for website_content.py (Task 2).

validate_and_fetch_website() makes a real HTTP request, so its own
integration behavior is tested via mocking requests.get/head — no real
network calls in this test file. extract_text_content() and
find_volunteer_link() are pure functions tested directly against
sample HTML.
"""
from unittest.mock import patch, MagicMock
from scripts.discovery.website_content import (
    validate_and_fetch_website,
    extract_text_content,
    find_volunteer_link,
)


SAMPLE_HTML = """
<html><head><title>Tech For Good Foundation</title></head>
<body>
<nav><a href="/about">About</a><a href="/volunteer">Volunteer With Us</a><a href="/donate">Donate</a></nav>
<main>
<h1>Tech For Good Foundation</h1>
<p>We provide free coding bootcamps and laptop donations to underserved youth
in San Francisco. Since 2015, we've trained over 400 students through our
after-school Saturday Robotics Academy program.</p>
</main>
</body></html>
"""

NO_VOLUNTEER_HTML = """
<html><body><nav><a href="/about">About</a><a href="/donate">Donate</a></nav>
<p>Some org content here.</p></body></html>
"""


def test_extract_text_content_strips_html_tags():
    text = extract_text_content(SAMPLE_HTML)
    assert "coding bootcamps" in text
    assert "Saturday Robotics Academy" in text
    assert "<p>" not in text
    assert "<nav>" not in text


def test_extract_text_content_empty_html_returns_empty_string():
    assert extract_text_content("") == ""
    assert extract_text_content("<html></html>") == ""


def test_find_volunteer_link_detects_volunteer_page():
    link = find_volunteer_link(SAMPLE_HTML, base_url="https://techforgood.org")
    assert link == "https://techforgood.org/volunteer"


def test_find_volunteer_link_returns_none_when_absent():
    link = find_volunteer_link(NO_VOLUNTEER_HTML, base_url="https://someorg.org")
    assert link is None


def test_find_volunteer_link_handles_get_involved_phrasing():
    html = '<a href="/get-involved">Get Involved</a>'
    link = find_volunteer_link(html, base_url="https://someorg.org")
    assert link == "https://someorg.org/get-involved"


@patch('scripts.website_content.requests.get')
def test_validate_and_fetch_website_success(mock_get, test_db):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = SAMPLE_HTML
    mock_resp.content = SAMPLE_HTML.encode()
    mock_get.return_value = mock_resp

    result = validate_and_fetch_website(
        db_con=test_db,
        ein='611234567',
        org_name='Tech For Good Foundation',
        candidate_url='techforgood.org'
    )

    assert result is not None
    assert result['identity_level'] in ('exact', 'strong')
    assert "coding bootcamps" in result['content_text']
    assert result['volunteer_url'] == 'https://techforgood.org/volunteer'


@patch('scripts.website_content.requests.get')
def test_validate_and_fetch_website_identity_mismatch_returns_none(mock_get, test_db):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "<html><body>Completely unrelated content about something else.</body></html>"
    mock_resp.content = mock_resp.text.encode()
    mock_get.return_value = mock_resp

    result = validate_and_fetch_website(
        db_con=test_db,
        ein='611234567',
        org_name='Tech For Good Foundation',
        candidate_url='wrongsite.org'
    )

    assert result is None


@patch('scripts.website_content.requests.get')
def test_validate_and_fetch_website_connection_error_returns_none(mock_get, test_db):
    import requests
    mock_get.side_effect = requests.exceptions.ConnectionError("refused")

    result = validate_and_fetch_website(
        db_con=test_db,
        ein='611234567',
        org_name='Tech For Good Foundation',
        candidate_url='doesnotexist.org'
    )

    assert result is None


@patch('scripts.website_content.requests.get')
def test_validate_and_fetch_website_caches_page(mock_get, test_db):
    """Confirms the fetched page gets cached via page_cache (reused schema)."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = SAMPLE_HTML
    mock_resp.content = SAMPLE_HTML.encode()
    mock_get.return_value = mock_resp

    cursor = test_db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS page_cache (
            url TEXT PRIMARY KEY, ein TEXT, fetched_at TEXT,
            status_code INTEGER, html_gz BLOB, content_len INTEGER
        )
    """)
    test_db.commit()

    validate_and_fetch_website(
        db_con=test_db, ein='611234567',
        org_name='Tech For Good Foundation', candidate_url='techforgood.org'
    )

    cursor.execute("SELECT COUNT(*) FROM page_cache WHERE ein = ?", ('611234567',))
    assert cursor.fetchone()[0] == 1
