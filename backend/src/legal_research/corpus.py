"""Local official-PDF collection and transparent lexical retrieval.

This is a deterministic baseline, not a language-model agent or legal relevance
judgment. Stored page text can contain syllabus, majority, and separate opinions.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
from typing import Iterable

STOP_WORDS = frozenset('a an and are as at be been by can could did do does for from had has have how i if in into is it its may of on or our should than that the their then there these they this those to under was were what when whether which who will with would you your find cases case decisions court supreme addressing involving compare'.split())


def terms(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2 and w not in STOP_WORDS]


def excerpt(text: str, keywords: Iterable[str], max_chars: int = 900) -> str:
    """Return an exact contiguous slice, without silently repairing OCR."""
    positions = [match.start() for word in keywords for match in re.finditer(r'\b' + re.escape(word) + r'\b', text, re.I)]
    start = max(0, min(positions, default=0) - 150)
    if start:
        boundary = text.find(' ', start, start + 60)
        if boundary != -1:
            start = boundary + 1
    return text[start:start + max_chars]


class Corpus:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.cases: list[dict] = []
        self.collection: dict = {}
        self.error: str | None = None
        if self.path.exists():
            try:
                payload = json.loads(self.path.read_text(encoding='utf-8'))
                if payload.get('schema_version') != 1 or not isinstance(payload.get('cases'), list):
                    raise ValueError('invalid corpus structure')
                seen = set()
                for case in payload['cases']:
                    if not isinstance(case, dict) or not all(case.get(k) for k in ('id', 'case_name', 'court', 'decision_date', 'source_url')):
                        raise ValueError('invalid case record')
                    date.fromisoformat(case['decision_date'])
                    if case['id'] in seen or not isinstance(case.get('pages'), list):
                        raise ValueError('duplicate or invalid case')
                    if not all(isinstance(p.get('text'), str) and isinstance(p.get('pdf_page'), int) and p['pdf_page'] > 0 for p in case['pages']):
                        raise ValueError('invalid page record')
                    seen.add(case['id'])
                self.cases = payload['cases']
                self.collection = payload.get('collection', {})
            except (ValueError, TypeError, KeyError, AttributeError, OSError):
                self.error = 'invalid_corpus_index'

    @property
    def count(self) -> int:
        return len(self.cases)

    def status(self) -> dict:
        return {
            'mode': 'local_official_pdf_lexical_search',
            'case_count': self.count,
            'collection': self.collection,
            'error': self.error,
            'ready': self.count > 0 and self.error is None,
            'note': 'Curated historical demo collection. No live CourtListener search or model-generated analysis.',
        }

    def get_case(self, case_id: str) -> dict | None:
        return next((case for case in self.cases if case['id'] == case_id), None)

    def search(self, query: str, court: str, date_from: str, date_to: str,
               excluded_ids: Iterable[str] | None = None, limit: int = 5) -> list[dict]:
        start, end = date.fromisoformat(date_from), date.fromisoformat(date_to)
        if start > end:
            raise ValueError('date_from must not be after date_to')
        if not 1 <= limit <= 50:
            raise ValueError('limit must be between 1 and 50')
        keywords = list(dict.fromkeys(terms(query)))
        if not keywords:
            return []
        excluded = set(excluded_ids or [])
        ranked = []
        for case in self.cases:
            if case['id'] in excluded or (court and case['court'] != court):
                continue
            if not start <= date.fromisoformat(case['decision_date']) <= end:
                continue
            # Editorial seed text can aid navigation, but never becomes a quotation.
            metadata = ' '.join([case['case_name'], case.get('summary', ''), ' '.join(case.get('comparison_topics', []))]).replace('_', ' ')
            meta_counts = Counter(terms(metadata))
            page_scores = []
            all_matches = set()
            for page in case['pages']:
                counts = Counter(terms(page['text']))
                matching = [word for word in keywords if counts[word]]
                all_matches.update(matching)
                score = sum(1 + min(counts[word], 5) * .05 for word in matching)
                if score > 0:
                    page_scores.append((score, page, matching))
            # Require actual source-text hits; metadata-only matches do not qualify.
            if not page_scores:
                continue
            score = len(all_matches) + sum(min(meta_counts[word], 2) for word in keywords) * .75
            page_scores.sort(key=lambda item: (-item[0], item[1]['pdf_page']))
            passages = []
            for _, page, matching in page_scores[:2]:
                passages.append({
                    'text': excerpt(page['text'], matching),
                    'pdf_page': page['pdf_page'],
                    'source_url': case['source_url'] + '#page=' + str(page['pdf_page']),
                    'opinion_scope': page.get('opinion_scope', 'unsegmented_pdf_page'),
                    'page_text_sha256': page.get('text_sha256'),
                })
            matches = sorted(all_matches)
            ranked.append({
                **{key: case.get(key) for key in ('id', 'case_name', 'citation', 'court', 'decision_date', 'source_url', 'summary', 'pdf_sha256')},
                'summary_kind': 'editorial_seed_summary_not_generated_analysis',
                'passages': passages,
                'score': round(score, 4),
                'matched_terms': matches,
                'explanation': 'Source text matches: ' + ', '.join(matches[:12]) + '. Keyword match only; inspect the passages and opinion context to assess legal relevance.',
                'treatment_status': 'not_checked',
                'retrieval_mode': 'local_lexical',
            })
        return sorted(ranked, key=lambda case: (-case['score'], case['id']))[:limit]
