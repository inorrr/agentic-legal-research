"""Offline synthetic responses only. These tests make no live API-access claim."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

import pytest


spec = importlib.util.spec_from_file_location("courtlistener_probe", Path(__file__).resolve().parents[2] / "scripts" / "validate_courtlistener.py")
probe_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe_module)


CASE = {
    "cluster_id": 11,
    "caseName": "Synthetic case",
    "court_id": "scotus",
    "dateFiled": "2009-04-21",
    "citation": ["Synthetic citation"],
    "absolute_url": "/opinion/11/synthetic-case/",
    "opinions": [{"id": 22}],
}
OPINION = {
    "id": 22,
    "cluster": "https://www.courtlistener.com/api/rest/v4/clusters/11/",
    "type": "020lead",
    "html_with_citations": "<p>Synthetic evidence &amp; text.</p>",
    "plain_text": "Different fallback text.",
}
NEXT_URL = "https://www.courtlistener.com/api/rest/v4/search/?" + urlencode({
    "q": "automobile", "court": "scotus", "filed_after": "1980-01-01",
    "filed_before": "2020-12-31", "type": "o", "cursor": "next",
})


def fetcher(case=None, opinion=None, next_url=None):
    requests = []

    def fetch(url, token):
        requests.append((url, token))
        if "/search/" in url:
            return {"results": [deepcopy(CASE if case is None else case)], "next": next_url}
        return deepcopy(OPINION if opinion is None else opinion)

    return fetch, requests


def test_uses_opinion_id_not_cluster_and_never_persists_token_or_text():
    fetch, requests = fetcher()
    result = probe_module.probe("private-test-token", fetch=fetch)
    assert result["status"] == "passed"
    assert requests[1][0].endswith("/opinions/22/")
    assert result["opinions"][0]["text_field"] == "html_with_citations"
    serialized = json.dumps(result)
    assert "private-test-token" not in serialized
    assert "Synthetic evidence" not in serialized


@pytest.mark.parametrize("field,value,category", [
    ("court_id", "ca1", "court_filter_mismatch"),
    ("dateFiled", "2021-01-01", "date_filter_mismatch"),
    ("dateFiled", None, "date_missing_or_invalid"),
    ("cluster_id", None, "cluster_id_missing_or_invalid"),
    ("opinions", [{"id": None}], "opinion_id_missing_or_invalid"),
])
def test_rejects_missing_identity_and_changed_filters(field, value, category):
    case = {**CASE, field: value}
    fetch, requests = fetcher(case=case)
    result = probe_module.probe("token", fetch=fetch)
    assert result["errors"][0]["category"] == category
    assert len(requests) == 1
    assert result["status"] != "passed"


def test_missing_text_does_not_count_snippet_as_full_opinion():
    opinion = {**OPINION, "html_with_citations": "<p> </p>", "plain_text": "", "snippet": "A snippet is not full text."}
    fetch, _ = fetcher(opinion=opinion)
    result = probe_module.probe("token", fetch=fetch)
    assert result["status"] == "partial"
    assert result["opinions"] == []
    assert result["errors"][0]["category"] == "opinion_text_missing"


@pytest.mark.parametrize("url", [
    "https://attacker.example/api/rest/v4/search/",
    "http://www.courtlistener.com/api/rest/v4/search/",
    "https://www.courtlistener.com@attacker.example/api/rest/v4/search/",
    "https://www.courtlistener.com/api/rest/v4/dockets/",
])
def test_unsafe_next_link_never_receives_credentials(url):
    fetch, requests = fetcher(next_url=url)
    result = probe_module.probe("token", pages=2, fetch=fetch)
    assert len(requests) == 1
    assert result["errors"][0]["category"] == "unsafe_source_url"


def test_pagination_and_request_budget_are_bounded():
    fetch, requests = fetcher(next_url=NEXT_URL)
    result = probe_module.probe("token", pages=2, fetch=fetch)
    assert result["status"] == "passed"
    assert len(result["pages"]) == 2
    assert len(result["cases"]) == 1  # Same case on two pages is deduplicated.
    assert len(requests) == 3 <= result["request_budget"]


@pytest.mark.parametrize("next_url", [
    NEXT_URL.replace("court=scotus", "court=ca1"),
    "https://www.courtlistener.com/api/rest/v4/search/?cursor=next",
])
def test_pagination_cannot_drop_or_change_explicit_constraints(next_url):
    fetch, requests = fetcher(next_url=next_url)
    result = probe_module.probe("token", pages=2, fetch=fetch)
    assert len(requests) == 1
    assert result["errors"][0]["category"] == "pagination_constraints_changed"


@pytest.mark.parametrize("field,value,category", [
    ("id", 11, "opinion_id_mismatch"),
    ("cluster", "https://www.courtlistener.com/api/rest/v4/clusters/99/", "opinion_cluster_mismatch"),
])
def test_wrong_opinion_identity_is_rejected(field, value, category):
    fetch, _ = fetcher(opinion={**OPINION, field: value})
    result = probe_module.probe("token", fetch=fetch)
    assert result["errors"][0]["category"] == category


@pytest.mark.parametrize("error,category", [
    (HTTPError("https://example.test", 401, "secret response", {}, None), "authentication_required_or_invalid"),
    (HTTPError("https://example.test", 403, "secret response", {}, None), "access_forbidden"),
    (HTTPError("https://example.test", 429, "secret response", {}, None), "rate_limited"),
    (URLError(socket.gaierror(-2, "secret response")), "dns_failure"),
    (URLError(TimeoutError("secret response")), "timeout"),
])
def test_failures_have_safe_categories_without_response_leak(error, category):
    def fail(url, token):
        raise error

    result = probe_module.probe("private-token", fetch=fail)
    assert result["errors"][0]["category"] == category
    assert "secret response" not in json.dumps(result)
    assert "private-token" not in json.dumps(result)


def test_missing_token_makes_no_request_and_anonymous_never_sends_token():
    fetch, requests = fetcher()
    result = probe_module.probe(None, fetch=fetch)
    assert result["errors"][0]["category"] == "token_missing"
    assert requests == []
    result = probe_module.probe("ignored-token", anonymous=True, fetch=fetch)
    assert result["status"] == "anonymous_access_only"
    assert all(token is None for _, token in requests)


def test_text_falls_back_only_when_html_has_no_usable_text():
    field, text = probe_module.opinion_text({"html_with_citations": "<script>hidden</script>", "plain_text": "Real fallback"})
    assert (field, text) == ("plain_text", "Real fallback")
