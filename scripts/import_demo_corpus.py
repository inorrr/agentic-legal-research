#!/usr/bin/env python3
"""Import the six allowlisted official PDFs into an ignored local demo corpus.

No model/provider credentials are needed. Download failures are disclosed; no
mock text or metadata summary is substituted for missing source text.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 25 * 1024 * 1024
MAX_PAGES = 100
ALLOWED_HOSTS = {'www.govinfo.gov', 'tile.loc.gov'}


class ImportFailure(Exception):
    pass


def allowed_url(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme != 'https' or parts.netloc not in ALLOWED_HOSTS or parts.query or parts.fragment or not parts.path.endswith('.pdf'):
        raise ImportFailure('unsupported_source_url')
    if parts.netloc == 'www.govinfo.gov' and not parts.path.startswith('/content/pkg/USREPORTS-'):
        raise ImportFailure('unsupported_source_path')
    if parts.netloc == 'tile.loc.gov' and not parts.path.startswith('/storage-services/service/ll/usrep/'):
        raise ImportFailure('unsupported_source_path')
    return url


class SafeRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        allowed_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(url: str) -> bytes:
    request = Request(allowed_url(url), headers={'User-Agent': 'AgenticLegalResearch-DemoImport/0.1', 'Accept': 'application/pdf'})
    with build_opener(SafeRedirects()).open(request, timeout=20) as response:
        payload = response.read(MAX_BYTES + 1)
    if len(payload) > MAX_BYTES:
        raise ImportFailure('pdf_too_large')
    if not payload.startswith(b'%PDF-'):
        raise ImportFailure('not_a_pdf')
    return payload


def extract(seed: dict, payload: bytes) -> dict:
    from pypdf import PdfReader
    reader = PdfReader(BytesIO(payload))
    if reader.is_encrypted or not 1 <= len(reader.pages) <= MAX_PAGES:
        raise ImportFailure('unsupported_pdf')
    if len(reader.pages) != seed['official_pdf_page_count']:
        raise ImportFailure('unexpected_page_count')
    pinpoints = set()
    for entry in seed['majority_pinpoints']:
        pinpoints.update(range(entry['pdf_page_start'], entry['pdf_page_end'] + 1))
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ''
        pages.append({
            'pdf_page': number,
            'text': text,
            'text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
            'opinion_scope': ('contains_majority_pinpoint_not_opinion_segmented' if number in pinpoints else 'unsegmented_pdf_page_may_include_syllabus_or_separate_opinions'),
        })
    if sum(len(p['text'].strip()) for p in pages) < 500:
        raise ImportFailure('insufficient_extracted_text')
    return {
        **seed,
        'source_url': seed['official_pdf_url'],
        'source_kind': 'official_us_reports_pdf',
        'pdf_sha256': hashlib.sha256(payload).hexdigest(),
        'retrieved_at': datetime.now(timezone.utc).isoformat(),
        'extraction': 'pypdf_extract_text_original_no_ocr_repairs',
        'pages': pages,
    }


def import_corpus(seeds_path: Path, output_dir: Path, only: str | None = None) -> dict:
    from pypdf.errors import PdfReadError
    seeds = json.loads(seeds_path.read_text(encoding='utf-8'))
    output_dir.mkdir(parents=True, exist_ok=True)
    cases, failures = [], []
    # Rebuild from available cached PDFs as well as requested downloads. Never
    # silently retain stale text for a source that failed fresh extraction.
    for seed in seeds['cases']:
        case_id = seed['id']
        if not re.fullmatch(r'[a-z0-9_]+', case_id):
            raise ImportFailure('unsafe_case_id')
        target = output_dir / (case_id + '.pdf')
        if target.is_symlink():
            raise ImportFailure('symlink_pdf_target')
        try:
            if target.exists():
                if target.stat().st_size > MAX_BYTES:
                    raise ImportFailure('pdf_too_large')
                payload = target.read_bytes()
            elif only and case_id != only:
                continue
            else:
                payload = download(seed['official_pdf_url'])
            case = extract(seed, payload)
            if not target.exists():
                target.write_bytes(payload)
            cases.append(case)
        except (ImportFailure, HTTPError, URLError, OSError, PdfReadError, ValueError) as error:
            category = str(error) if isinstance(error, ImportFailure) else type(error).__name__
            failures.append({'case_id': case_id, 'error': category})
            print(f'{case_id}: {category}', file=sys.stderr)
    result = {
        'schema_version': 1,
        'collection': {**seeds['collection'], 'import_mode': 'official_pdf_local_cache', 'imported_count': len(cases), 'source_text_status': 'extracted_full_pdfs_unsegmented', 'imported_at': datetime.now(timezone.utc).isoformat()},
        'cases': cases,
        'failures': failures,
    }
    index = output_dir / 'index.json'
    if index.is_symlink():
        raise ImportFailure('symlink_index_target')
    temporary = output_dir / 'index.json.tmp'
    if temporary.is_symlink():
        raise ImportFailure('symlink_index_target')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(index)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds', type=Path, default=ROOT / 'examples/vehicle_search/seed_cases.json')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'data/corpus')
    parser.add_argument('--only', help='Download one seed ID; already-cached PDFs are still indexed.')
    args = parser.parse_args()
    try:
        result = import_corpus(args.seeds, args.output_dir, args.only)
    except ImportError:
        print('Install pypdf in the project environment before importing.', file=sys.stderr)
        return 1
    print(json.dumps({'imported': len(result['cases']), 'failed': len(result['failures']), 'index': str(args.output_dir / 'index.json')}))
    return 1 if result['failures'] or not result['cases'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
