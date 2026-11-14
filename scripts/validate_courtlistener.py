#!/usr/bin/env python3
"""Bounded live-access diagnostic, separate from the application source adapter.

No .env loading, model calls, retries, full-text storage, or credential logging.
The default run makes at most three requests (one search, two opinions).
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import getpass
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import socket
import ssl
import sys
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


BASE = "https://www.courtlistener.com"
SEARCH_PATH = "/api/rest/v4/search/"
COURT = "scotus"
START = "1980-01-01"
END = "2020-12-31"
MAX_RESPONSE_BYTES = 8 * 1024 * 1024


class ProbeError(Exception):
    """A safe, fixed diagnostic category, never a remote response or credential."""


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProbeError("redirect_rejected")


def validate_url(url: str, path: str) -> str:
    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or parts.netloc != "www.courtlistener.com"
        or parts.path != path
        or parts.fragment
    ):
        raise ProbeError("unsafe_source_url")
    return url


def validate_next_url(url: str, filters: dict) -> str:
    validate_url(url, SEARCH_PATH)
    query = parse_qs(urlsplit(url).query)
    for key, value in {"q": "automobile", **filters}.items():
        if query.get(key) != [value]:
            raise ProbeError("pagination_constraints_changed")
    return url


def fetch_json(url: str, token: str | None) -> dict:
    headers = {"Accept": "application/json", "User-Agent": "AgenticLegalResearch-Validation/0.1"}
    if token:
        headers["Authorization"] = f"Token {token}"
    request = Request(url, headers=headers)
    # Do not forward Authorization to an unexpected redirect target.
    with build_opener(NoRedirects()).open(request, timeout=20) as response:
        payload = response.read(MAX_RESPONSE_BYTES + 1)
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ProbeError("response_too_large")
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ProbeError("invalid_response_shape")
    return parsed


def error_category(error: Exception) -> str:
    if isinstance(error, ProbeError):
        return str(error)
    if isinstance(error, HTTPError):
        return {
            401: "authentication_required_or_invalid",
            403: "access_forbidden",
            429: "rate_limited",
        }.get(error.code, f"http_{error.code}")
    reason = error.reason if isinstance(error, URLError) else error
    if isinstance(reason, socket.gaierror):
        return "dns_failure"
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return "timeout"
    if isinstance(reason, ssl.SSLError):
        return "tls_failure"
    if isinstance(error, (json.JSONDecodeError, UnicodeDecodeError)):
        return "invalid_json"
    return "network_failure" if isinstance(error, (URLError, OSError)) else "unexpected_response"


class TextReader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.ignored_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.ignored_depth:
            self.ignored_depth -= 1

    def handle_data(self, data):
        if not self.ignored_depth:
            self.parts.append(data)


def opinion_text(opinion: dict) -> tuple[str, str]:
    html = opinion.get("html_with_citations")
    if isinstance(html, str) and html.strip():
        parser = TextReader()
        parser.feed(html)
        text = " ".join(" ".join(parser.parts).split())
        if text:
            return "html_with_citations", text
    plain = opinion.get("plain_text")
    if isinstance(plain, str) and plain.strip():
        return "plain_text", " ".join(plain.split())
    raise ProbeError("opinion_text_missing")


def positive_id(value) -> bool:
    return type(value) is int and value > 0


def case_summary(case: dict) -> dict:
    if case.get("court_id") != COURT:
        raise ProbeError("court_filter_mismatch")
    filed = case.get("dateFiled")
    try:
        parsed_date = date.fromisoformat(filed)
    except (TypeError, ValueError):
        raise ProbeError("date_missing_or_invalid") from None
    if not date.fromisoformat(START) <= parsed_date <= date.fromisoformat(END):
        raise ProbeError("date_filter_mismatch")
    cluster_id = case.get("cluster_id")
    if not positive_id(cluster_id):
        raise ProbeError("cluster_id_missing_or_invalid")
    name = case.get("caseName")
    if not isinstance(name, str) or not name.strip():
        raise ProbeError("case_name_missing")
    relative = case.get("absolute_url")
    if not isinstance(relative, str) or not relative.startswith(f"/opinion/{cluster_id}/"):
        raise ProbeError("case_source_link_mismatch")
    # Require a local path; never silently accept a server-supplied external URL.
    parts = urlsplit(relative)
    if parts.scheme or parts.netloc or parts.query or parts.fragment:
        raise ProbeError("case_source_link_mismatch")
    nested = case.get("opinions")
    if not isinstance(nested, list) or not nested:
        raise ProbeError("opinion_ids_missing")
    if any(not isinstance(item, dict) or not positive_id(item.get("id")) for item in nested):
        raise ProbeError("opinion_id_missing_or_invalid")
    citations = case.get("citation")
    if not isinstance(citations, list) or not all(isinstance(c, str) for c in citations):
        raise ProbeError("citation_metadata_invalid")
    return {
        "cluster_id": cluster_id,
        "case_name": name,
        "court_id": COURT,
        "date_filed": filed,
        "citations": citations,
        "source_url": BASE + relative,
        "opinion_ids": [item["id"] for item in nested],
    }


def probe(
    token: str | None,
    *,
    anonymous: bool = False,
    pages: int = 1,
    max_opinions: int = 2,
    fetch: Callable[[str, str | None], dict] = fetch_json,
) -> dict:
    if pages not in (1, 2) or max_opinions not in (1, 2):
        raise ValueError("pages and max_opinions must each be 1 or 2")
    if anonymous:
        token = None
    report = {
        "schema_version": 1,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "mode": "anonymous_diagnostic" if anonymous else "authenticated",
        "status": "blocked",
        "scope": "Sample access only; no completeness, treatment, or legal correctness validation.",
        "filters": {"court": COURT, "filed_after": START, "filed_before": END, "type": "o"},
        "query": "automobile",
        "request_budget": pages + max_opinions,
        "requests_attempted": 0,
        "pages": [],
        "cases": [],
        "opinions": [],
        "errors": [],
    }
    if not anonymous and not token:
        report["errors"].append({"stage": "configuration", "category": "token_missing"})
        return report
    url = BASE + SEARCH_PATH + "?" + urlencode({"q": "automobile", **report["filters"], "order_by": "score desc"})
    stage = "search"
    try:
        for page_number in range(1, pages + 1):
            validate_url(url, SEARCH_PATH)
            report["requests_attempted"] += 1
            page = fetch(url, token)
            results = page.get("results")
            if not isinstance(results, list):
                raise ProbeError("search_results_missing")
            next_url = page.get("next")
            if next_url is not None:
                if not isinstance(next_url, str):
                    raise ProbeError("invalid_pagination_link")
                validate_next_url(next_url, report["filters"])
            report["pages"].append({"number": page_number, "result_count": len(results), "next_present": bool(next_url)})
            for case in results:
                if not isinstance(case, dict):
                    raise ProbeError("invalid_case_shape")
                summary = case_summary(case)
                if summary["cluster_id"] not in {c["cluster_id"] for c in report["cases"]}:
                    report["cases"].append(summary)
            if not next_url:
                break
            url = next_url
        if not report["cases"]:
            raise ProbeError("no_search_results")
        stage = "opinion"
        candidates = [(c["cluster_id"], o) for c in report["cases"] for o in c["opinion_ids"]]
        for cluster_id, opinion_id in candidates[:max_opinions]:
            path = f"/api/rest/v4/opinions/{opinion_id}/"
            url = validate_url(BASE + path, path)
            report["requests_attempted"] += 1
            opinion = fetch(url, token)
            if opinion.get("id") != opinion_id:
                raise ProbeError("opinion_id_mismatch")
            if opinion.get("cluster") != f"{BASE}/api/rest/v4/clusters/{cluster_id}/":
                raise ProbeError("opinion_cluster_mismatch")
            field, text = opinion_text(opinion)
            report["opinions"].append({
                "cluster_id": cluster_id,
                "opinion_id": opinion_id,
                "opinion_type": opinion.get("type"),
                "api_url": url,
                "text_field": field,
                "normalized_text_characters": len(text),
                "normalized_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            })
        report["status"] = "passed" if token else "anonymous_access_only"
    except Exception as error:
        report["status"] = "partial" if report["cases"] else "blocked"
        report["errors"].append({"stage": stage, "category": error_category(error)})
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    credential = parser.add_mutually_exclusive_group()
    credential.add_argument("--prompt-token", action="store_true", help="Read a token privately from the terminal.")
    credential.add_argument("--anonymous", action="store_true", help="Unauthenticated diagnostic; cannot validate account access.")
    parser.add_argument("--pages", type=int, choices=(1, 2), default=1)
    parser.add_argument("--max-opinions", type=int, choices=(1, 2), default=2)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "courtlistener-access-check.json")
    args = parser.parse_args()
    if args.prompt_token and not sys.stdin.isatty():
        parser.error("--prompt-token requires an interactive terminal; use an environment token otherwise")
    token = getpass.getpass("CourtListener API token: ") if args.prompt_token else os.environ.get("COURTLISTENER_API_TOKEN")
    report = probe(token.strip() if token else None, anonymous=args.anonymous, pages=args.pages, max_opinions=args.max_opinions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "requests_attempted": report["requests_attempted"], "errors": report["errors"], "report": str(args.output)}))
    return 0 if report["status"] in {"passed", "anonymous_access_only"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
