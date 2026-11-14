"""Bounded CourtListener case search with lazy, attributable local snapshots.

Credentials remain in memory. Search records and opinion text are untrusted data;
only fixed HTTPS API endpoints receive credentials. Cached text sections are local
navigation units, never invented PDF pages or reporter pinpoints.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
import sqlite3
import time
from urllib.parse import parse_qs, urlencode, urlsplit

import httpx


BASE = 'https://www.courtlistener.com'
SEARCH_PATH = '/api/rest/v4/search/'
MAX_BYTES = 8 * 1024 * 1024
SEARCH_CACHE_SECONDS = 24 * 60 * 60
MISSING_TEXT_CACHE_SECONDS = 24 * 60 * 60
RATE_WINDOWS = ((60, 5), (3600, 50), (86400, 125))


class SourceError(Exception):
    """Fixed public diagnostics only; never include provider bodies or tokens."""
    def __init__(self, category: str, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.category = category
        self.message = message
        self.retry_after = retry_after


def _error(category, message):
    return SourceError(category, message)


def _positive(value):
    return type(value) is int and value > 0


def _api_url(url: str, path: str) -> str:
    try:
        parts = urlsplit(url)
    except (TypeError, ValueError):
        raise _error('unsafe_source_url', 'The source supplied an unsafe API URL.') from None
    if (parts.scheme != 'https' or parts.netloc != 'www.courtlistener.com'
            or parts.path != path or parts.fragment):
        raise _error('unsafe_source_url', 'The source supplied an unsafe API URL.')
    return url


def _next_url(value, parameters):
    if value is None:
        return None
    if not isinstance(value, str):
        raise _error('invalid_response', 'The source returned invalid pagination metadata.')
    _api_url(value, SEARCH_PATH)
    query = parse_qs(urlsplit(value).query, keep_blank_values=True)
    if any(query.get(key) != [item] for key, item in parameters.items()):
        raise _error('pagination_constraints_changed', 'Source pagination changed the query or explicit filters.')
    if set(query) - (set(parameters) | {'cursor', 'page'}) or any(len(items) != 1 for items in query.values()):
        raise _error('pagination_constraints_changed', 'Source pagination contains unexpected parameters.')
    return value


class _TextReader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored = 0

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style'}:
            self.ignored += 1

    def handle_endtag(self, tag):
        if tag in {'script', 'style'} and self.ignored:
            self.ignored -= 1

    def handle_data(self, text):
        if not self.ignored:
            self.parts.append(text)


def _text(record):
    for field in ('html_with_citations', 'plain_text', 'html', 'html_lawbox', 'html_columbia', 'xml_harvard'):
        content = record.get(field)
        if not isinstance(content, str) or not content.strip():
            continue
        if field == 'plain_text':
            text = content
            kind = 'plain_text'
        else:
            reader = _TextReader()
            reader.feed(content)
            text = ' '.join(' '.join(reader.parts).split())
            kind = 'normalized_html_text'
        if text.strip():
            return text, field, kind
    raise _error('opinion_text_missing', 'This source record has no usable opinion text.')


def _opinion_scope(value):
    raw = value if isinstance(value, str) else ''
    if 'combined' in raw:
        return 'combined_opinion_may_include_separate_opinions'
    if 'dissent' in raw:
        return 'dissenting_opinion'
    if 'concurr' in raw:
        return 'concurring_opinion'
    if 'lead' in raw:
        return 'lead_opinion'
    return 'unknown_opinion_type_verify_source'


def _opinion_priority(item):
    kind = str(item.get('type', ''))
    if 'lead' in kind:
        return 0
    if 'combined' in kind:
        return 1
    if 'dissent' in kind:
        return 4
    if 'concurr' in kind:
        return 3
    return 2


def _case(record, court, start, end):
    if not isinstance(record, dict):
        raise _error('invalid_response', 'The source returned an invalid case record.')
    cluster = record.get('cluster_id')
    case_court = record.get('court_id')
    filed = record.get('dateFiled')
    try:
        when = date.fromisoformat(filed)
    except (TypeError, ValueError):
        raise _error('filter_mismatch', 'A source result lacks a verifiable decision date.') from None
    if not isinstance(case_court, str) or not case_court or (court != 'all' and case_court != court) or not start <= when <= end:
        raise _error('filter_mismatch', 'A source result did not satisfy the fixed court/date filters.')
    name = record.get('caseName')
    if not _positive(cluster) or not isinstance(name, str) or not name.strip():
        raise _error('invalid_response', 'The source returned invalid case identity metadata.')
    relative = record.get('absolute_url')
    if not isinstance(relative, str) or not relative.startswith(f'/opinion/{cluster}/'):
        raise _error('unsafe_source_url', 'The source case link does not match its identity.')
    parts = urlsplit(relative)
    if parts.scheme or parts.netloc or parts.query or parts.fragment:
        raise _error('unsafe_source_url', 'The source case link is not an expected local path.')
    opinions = record.get('opinions')
    if (not isinstance(opinions, list) or not opinions
            or any(not isinstance(o, dict) or not _positive(o.get('id')) for o in opinions)):
        raise _error('invalid_response', 'The source did not identify the case opinions.')
    citations = record.get('citation') or []
    if not isinstance(citations, list) or any(not isinstance(c, str) for c in citations):
        raise _error('invalid_response', 'The source returned invalid citation metadata.')
    return {
        'id': f'cl-{cluster}', 'cluster_id': cluster, 'case_name': name,
        'citation': '; '.join(citations), 'court': case_court,
        'court_name': str(record.get('court') or case_court), 'decision_date': filed,
        'source_url': BASE + relative, 'source_provider': 'CourtListener',
        'summary': '', 'passages': [], 'score': 0,
        'opinion_ids': [o['id'] for o in opinions],
        'opinions': [{'id': o['id'], 'type': str(o.get('type') or '')[:100]} for o in opinions],
        'retrieval_mode': 'courtlistener', 'treatment_status': 'not_checked',
        'explanation': 'Matched the CourtListener search query. Read the opinion to assess its relevance; search rank is not a legal conclusion.',
        'explanation_kind': 'source_search_match_not_legal_analysis',
    }


class CourtListenerSource:
    source_mode = 'courtlistener'

    def __init__(self, cache_path: Path, token: str, *, request_budget=4, _client=None, _clock=time.time):
        if not isinstance(token, str) or not token.strip():
            raise _error('authentication_required', 'Configure your CourtListener token before searching this source.')
        if type(request_budget) is not int or not 1 <= request_budget <= 4:
            raise ValueError('Source request budget must be between one and four.')
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._token = token
        self._clock = _clock
        self.request_budget = request_budget
        self.metrics = {'api_requests': 0, 'cache_hits': 0}
        self.actions = []
        self.last_search = {}
        self._owned_client = _client is None
        try:
            self._client = _client if _client is not None else httpx.Client(timeout=20, follow_redirects=False)
        except Exception:
            raise _error('client_configuration_error', 'The source client could not start; check local network configuration.') from None
        with self._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS source_search_pages(url TEXT PRIMARY KEY, fetched REAL NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS source_cases(id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS source_opinions(opinion_id INTEGER PRIMARY KEY, fetched REAL NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS source_requests(at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS source_limits(id INTEGER PRIMARY KEY CHECK(id=1), blocked_until REAL NOT NULL);
            ''')

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.cache_path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def close(self):
        if self._owned_client:
            try:
                self._client.close()
            except Exception:
                pass

    def _reserve_request(self):
        if self.metrics['api_requests'] >= self.request_budget:
            raise _error('source_budget', 'This round reached its CourtListener request budget. Start another round to continue.')
        now = self._clock()
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            blocked = db.execute('SELECT blocked_until FROM source_limits WHERE id=1').fetchone()
            if blocked and blocked[0] > now:
                wait = max(1, math.ceil(blocked[0] - now))
                raise SourceError('rate_limited', 'CourtListener requested a pause before further source requests.', wait)
            db.execute('DELETE FROM source_requests WHERE at<=?', (now-86400,))
            for window, allowance in RATE_WINDOWS:
                rows = [r[0] for r in db.execute('SELECT at FROM source_requests WHERE at>? ORDER BY at', (now-window,))]
                if len(rows) >= allowance:
                    wait = max(1, math.ceil(rows[len(rows)-allowance]+window-now))
                    raise SourceError('rate_limited', 'The local CourtListener request allowance is temporarily exhausted.', wait)
            db.execute('INSERT INTO source_requests(at) VALUES (?)', (now,))
        self.metrics['api_requests'] += 1

    def _retry_seconds(self, value):
        try:
            seconds = float(value)
            if math.isfinite(seconds):
                return max(1, min(86400, math.ceil(seconds)))
        except (TypeError, ValueError):
            pass
        try:
            return max(1, min(86400, math.ceil(parsedate_to_datetime(value).timestamp()-self._clock())))
        except (TypeError, ValueError, OverflowError):
            return 60

    def _fetch(self, url, path):
        _api_url(url, path)
        self._reserve_request()
        headers = {'Accept': 'application/json', 'Authorization': f'Token {self._token}',
                   'User-Agent': 'Casework-LegalResearch/0.3'}
        try:
            with self._client.stream('GET', url, headers=headers, timeout=20, follow_redirects=False) as response:
                status = response.status_code
                if status == 429:
                    retry = self._retry_seconds(response.headers.get('Retry-After'))
                    with self._db() as db:
                        db.execute('INSERT INTO source_limits VALUES (1,?) ON CONFLICT(id) DO UPDATE SET blocked_until=max(blocked_until,excluded.blocked_until)', (self._clock()+retry,))
                    raise SourceError('rate_limited', 'CourtListener rate-limited this request. Wait before searching again.', retry)
                if status in {401, 403}:
                    raise _error('authentication_required' if status == 401 else 'access_forbidden',
                                 'CourtListener rejected the configured access. Check your token and account permissions.')
                if 300 <= status < 400:
                    raise _error('unsafe_source_url', 'A source redirect was rejected; credentials were not forwarded.')
                if status >= 400:
                    raise _error('source_unavailable', 'CourtListener could not complete this source request.')
                length = response.headers.get('Content-Length', '')
                if length.isdigit() and int(length) > MAX_BYTES:
                    raise _error('response_too_large', 'The source response exceeded the allowed size.')
                body = bytearray()
                for chunk in response.iter_bytes(chunk_size=65536):
                    body.extend(chunk)
                    if len(body) > MAX_BYTES:
                        raise _error('response_too_large', 'The source response exceeded the allowed size.')
                payload = json.loads(body)
        except SourceError:
            raise
        except (ValueError, UnicodeError):
            raise _error('invalid_response', 'CourtListener returned an unreadable response.') from None
        except Exception:
            raise _error('network_error', 'CourtListener could not be reached. Check your connection and try later.') from None
        if not isinstance(payload, dict):
            raise _error('invalid_response', 'CourtListener returned an invalid response structure.')
        return payload

    def _search_page(self, url, parameters, court, start, end):
        with self._db() as db:
            row = db.execute('SELECT fetched,body FROM source_search_pages WHERE url=?', (url,)).fetchone()
        if row and self._clock()-row[0] < SEARCH_CACHE_SECONDS:
            self.metrics['cache_hits'] += 1
            page = json.loads(row[1])
            _next_url(page.get('next'), parameters)
            return page
        raw = self._fetch(url, SEARCH_PATH)
        results = raw.get('results')
        if not isinstance(results, list) or len(results) > 100:
            raise _error('invalid_response', 'CourtListener returned an invalid result list.')
        fetched_at = datetime.fromtimestamp(self._clock(), timezone.utc).isoformat()
        cases = [{**_case(item, court, start, end), 'source_fetched_at': fetched_at} for item in results]
        page = {'cases': cases, 'next': _next_url(raw.get('next'), parameters),
                'count': raw.get('count') if type(raw.get('count')) is int else None,
                'fetched_at': fetched_at}
        with self._db() as db:
            db.execute('INSERT INTO source_search_pages VALUES (?,?,?) ON CONFLICT(url) DO UPDATE SET fetched=excluded.fetched,body=excluded.body', (url,self._clock(),json.dumps(page)))
            for case in cases:
                db.execute('INSERT INTO source_cases VALUES (?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body', (case['id'],json.dumps(case)))
        return page

    def _text_availability(self, case):
        """Negative cache metadata never implies evidence has been delivered."""
        ids = [opinion['id'] for opinion in case['opinions']]
        placeholders = ','.join('?' for _ in ids)
        with self._db() as db:
            records = db.execute(f'SELECT opinion_id,fetched,body FROM source_opinions WHERE opinion_id IN ({placeholders})', ids).fetchall()
        unavailable, available = [], False
        for opinion_id, fetched, body in records:
            snapshot = json.loads(body)
            if snapshot.get('opinion_id') != opinion_id or snapshot.get('cluster_id') != case['cluster_id']:
                raise _error('opinion_identity_mismatch', 'The cached opinion does not belong to the selected case.')
            if snapshot.get('text_status') == 'unavailable':
                if self._clock()-fetched < MISSING_TEXT_CACHE_SECONDS:
                    unavailable.append(opinion_id)
            elif snapshot.get('canonical_text'):
                available = True
        missing = len(unavailable) == len(ids)
        return {'text_status': 'unavailable' if missing else 'not_read',
                'text_availability': 'unavailable' if missing else 'cached' if available else 'not_fetched',
                'unavailable_opinion_ids': unavailable}

    def search(self, query, court, date_from, date_to, excluded_ids=None, limit=5):
        if not isinstance(query, str) or not query.strip() or len(query) > 1200:
            raise ValueError('Search query must contain one to 1200 characters.')
        if court != 'all' and (not isinstance(court, str) or not re.fullmatch(r'[a-z0-9]{1,32}', court)):
            raise ValueError('Invalid court filter.')
        start, end = date.fromisoformat(date_from), date.fromisoformat(date_to)
        if start > end or type(limit) is not int or not 1 <= limit <= 50:
            raise ValueError('Invalid date range or result limit.')
        parameters = {'q': query, 'type': 'o', 'filed_after': date_from,
                      'filed_before': date_to, 'order_by': 'score desc'}
        if court != 'all':
            parameters['court'] = court
        url = BASE + SEARCH_PATH + '?' + urlencode(parameters)
        excluded = set(excluded_ids or [])
        found, visited = {}, set()
        self.last_search = {'count': None, 'has_more': False, 'pages_examined': 0}
        while url and len(visited) < 25:
            if url in visited:
                raise _error('invalid_response', 'CourtListener repeated a pagination cursor.')
            visited.add(url)
            try:
                page = self._search_page(url, parameters, court, start, end)
            except SourceError as error:
                if not found or error.category not in {'source_budget', 'rate_limited'}:
                    raise
                self.last_search.update(has_more=True, stopped_reason=error.message, error_category=error.category, retry_after=error.retry_after)
                break
            self.last_search.update(count=page['count'], pages_examined=len(visited))
            for case in page['cases']:
                # Cached search pages are keyed by the entire immutable query/filter URL.
                if (court != 'all' and case['court'] != court) or not date_from <= case['decision_date'] <= date_to:
                    raise _error('filter_mismatch', 'A cached result does not match the fixed filters.')
                found.setdefault(case['id'], {**case, **self._text_availability(case)})
            url = page['next']
            usable_new = sum(key not in excluded and case['text_status'] != 'unavailable' for key, case in found.items())
            self.last_search['has_more'] = bool(url) or usable_new > limit
            if usable_new >= limit:
                break
        if url and len(visited) >= 25:
            self.last_search.update(has_more=True, stopped_reason='Stopped at the bounded pagination scan limit.')
        ordered = sorted(found.values(), key=lambda case: (case['text_status'] == 'unavailable', case['id'] in excluded))
        self.last_search['known_unavailable_count'] = sum(case['text_status'] == 'unavailable' for case in found.values())
        self.actions.append({'tool':'courtlistener_search','detail':f"Searched CourtListener with fixed filters; examined {len(visited)} page(s), retained {len(found)} distinct candidates."})
        return [{**case, 'score': float(len(ordered)-index)}
                for index, case in enumerate(ordered[:limit])]

    def get_case(self, case_id):
        if not isinstance(case_id, str) or not re.fullmatch(r'cl-[1-9][0-9]*', case_id):
            return None
        with self._db() as db:
            row = db.execute('SELECT body FROM source_cases WHERE id=?', (case_id,)).fetchone()
        if row is None:
            return None
        case = json.loads(row[0])
        unavailable = set(self._text_availability(case)['unavailable_opinion_ids'])
        opinion = min([item for item in case['opinions'] if item['id'] not in unavailable] or case['opinions'], key=_opinion_priority)
        opinion_id = opinion['id']
        with self._db() as db:
            cached = db.execute('SELECT fetched,body FROM source_opinions WHERE opinion_id=?', (opinion_id,)).fetchone()
        if cached:
            snapshot = json.loads(cached[1])
            if snapshot.get('opinion_id') != opinion_id or snapshot.get('cluster_id') != case['cluster_id']:
                raise _error('opinion_identity_mismatch', 'The cached opinion does not belong to the selected case.')
            if snapshot.get('text_status') == 'unavailable':
                if self._clock()-cached[0] < MISSING_TEXT_CACHE_SECONDS:
                    self.metrics['cache_hits'] += 1
                    raise _error('opinion_text_missing', 'This source record has no usable opinion text; the recent check is cached.')
                cached = None
        if cached:
            self.metrics['cache_hits'] += 1
        else:
            path = f'/api/rest/v4/opinions/{opinion_id}/'
            record = self._fetch(BASE + path, path)
            if record.get('id') != opinion_id or record.get('cluster') != f"{BASE}/api/rest/v4/clusters/{case['cluster_id']}/":
                raise _error('opinion_identity_mismatch', 'The retrieved opinion does not belong to the selected case.')
            try:
                text, field, kind = _text(record)
            except SourceError as error:
                if error.category == 'opinion_text_missing':
                    missing = {'opinion_id': opinion_id, 'cluster_id': case['cluster_id'],
                               'text_status': 'unavailable',
                               'source_fetched_at': datetime.fromtimestamp(self._clock(), timezone.utc).isoformat()}
                    with self._db() as db:
                        db.execute('INSERT INTO source_opinions VALUES (?,?,?) ON CONFLICT(opinion_id) DO UPDATE SET fetched=excluded.fetched,body=excluded.body', (opinion_id,self._clock(),json.dumps(missing)))
                raise
            snapshot = {'opinion_id': opinion_id, 'cluster_id': case['cluster_id'],
                        'canonical_text': text, 'text_field': field, 'text_kind': kind,
                        'opinion_type': str(record.get('type') or opinion['type'])[:100],
                        'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
                        'source_fetched_at': datetime.fromtimestamp(self._clock(), timezone.utc).isoformat()}
            with self._db() as db:
                db.execute('INSERT INTO source_opinions VALUES (?,?,?) ON CONFLICT(opinion_id) DO UPDATE SET fetched=excluded.fetched,body=excluded.body', (opinion_id,self._clock(),json.dumps(snapshot)))
        if snapshot['cluster_id'] != case['cluster_id']:
            raise _error('opinion_identity_mismatch', 'The cached opinion does not belong to the selected case.')
        text = snapshot['canonical_text']
        scope = _opinion_scope(snapshot['opinion_type'])
        sections = []
        for index, start in enumerate(range(0, len(text), 2500), 1):
            end = min(start+2500, len(text))
            section_text = text[start:end]
            sections.append({'section_number': index, 'text': section_text,
                             'text_start': start, 'text_end': end,
                             'source_url': case['source_url'], 'opinion_id': opinion_id,
                             'opinion_scope': scope, 'text_sha256': snapshot['text_sha256'],
                             'section_text_sha256': hashlib.sha256(section_text.encode()).hexdigest(),
                             'locator_label': f'Opinion {opinion_id}, text section {index}'})
        self.actions.append({'tool':'courtlistener_read','detail':f'Read opinion {opinion_id} for {case_id}; retained an attributable text snapshot.'})
        return {**case, **snapshot, 'sections': sections, 'opinion_scope': scope,
                'short_record': len(text.strip()) < 500,
                'text_status': 'short_record' if len(text.strip()) < 500 else 'opinion_text',
                'opinion_selection_note': 'One lead/combined or available opinion snapshot; other separate opinions have not been loaded.'}
