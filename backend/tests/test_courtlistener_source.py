"""CourtListener adapter behavior using synthetic records and mocked HTTP only."""
import json
import sqlite3

import httpx
import pytest

from legal_research.courtlistener import CourtListenerSource, SourceError


TOKEN = 'synthetic-not-a-real-token'
NOW = 1_700_000_000.0


def case(number=1, *, court='scotus', filed='1999-04-05', opinions=None):
    cluster = 100 + number
    return {
        'cluster_id': cluster, 'caseName': f'Synthetic Case {number}',
        'court_id': court, 'court': 'Synthetic Court', 'dateFiled': filed,
        'absolute_url': f'/opinion/{cluster}/synthetic-case-{number}/',
        'citation': [f'{number} TEST 100'],
        'opinions': opinions or [{'id': 1000 + number, 'type': 'lead-opinion'}],
    }


def opinion(number=1, *, text=None, opinion_id=None, kind='020lead'):
    return {
        'id': opinion_id or 1000 + number,
        'cluster': f'https://www.courtlistener.com/api/rest/v4/clusters/{100 + number}/',
        'type': kind,
        'html_with_citations': text or '<p>' + ('Synthetic vehicle source evidence. ' * 250) + '</p>',
        'plain_text': '',
    }


def page(records=None, next_url=None):
    records = [case()] if records is None else records
    return {'count': len(records), 'next': next_url, 'results': records}


def source(tmp_path, handler, **kwargs):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return CourtListenerSource(tmp_path / 'source.sqlite3', TOKEN, _client=client,
                               _clock=kwargs.pop('_clock', lambda: NOW), **kwargs)


def search(adapter, *, query='vehicle', court='scotus', excluded_ids=None, limit=5):
    return adapter.search(query, court=court, date_from='1980-01-01', date_to='2020-12-31',
                          excluded_ids=excluded_ids, limit=limit)


def test_search_is_lazy_and_metadata_does_not_become_source_evidence(tmp_path):
    requests = []

    def handler(request):
        requests.append(request)
        assert request.url.host == 'www.courtlistener.com'
        assert request.headers['authorization'] == f'Token {TOKEN}'
        assert request.url.path == '/api/rest/v4/search/'
        assert request.url.params['court'] == 'scotus'
        assert request.url.params['filed_after'] == '1980-01-01'
        assert request.url.params['filed_before'] == '2020-12-31'
        return httpx.Response(200, json=page())

    adapter = source(tmp_path, handler)
    try:
        found = search(adapter)
        assert len(requests) == 1
        assert found[0]['id'] == 'cl-101'
        assert found[0]['passages'] == []
        assert found[0]['retrieval_mode'] == 'courtlistener'
        assert adapter.metrics['api_requests'] == 1
    finally:
        adapter.close()


def test_reads_one_preferred_opinion_and_keeps_exact_text_sections(tmp_path):
    paths = []
    records = [case(opinions=[{'id': 2001, 'type': 'dissent'},
                             {'id': 1001, 'type': 'lead-opinion'}])]

    def handler(request):
        paths.append(request.url.path)
        if request.url.path.endswith('/search/'):
            return httpx.Response(200, json=page(records))
        assert request.url.path == '/api/rest/v4/opinions/1001/'
        return httpx.Response(200, json=opinion(text='<script>not evidence</script><p>' +
                                               'Exact canonical words &amp; punctuation. ' * 250 + '</p>'))

    adapter = source(tmp_path, handler)
    try:
        search(adapter)
        full = adapter.get_case('cl-101')
        assert len(paths) == 2
        assert full['sections']
        canonical = full['canonical_text']
        assert 'not evidence' not in canonical
        assert '&amp;' not in canonical
        assert len(full['sections']) >= 2
        for section in full['sections']:
            assert section['text'] == canonical[section['text_start']:section['text_end']]
            assert section['opinion_id'] == 1001
            assert section['opinion_scope']
            assert section['text_sha256']
            assert section['locator_label']
            assert 'pdf_page' not in section
            assert '#page=' not in section['source_url']
        assert adapter.get_case('cl-101')['sections'] == full['sections']
        assert len(paths) == 2
    finally:
        adapter.close()


def test_cache_reused_across_instances_without_http(tmp_path):
    def handler(request):
        return httpx.Response(200, json=page() if request.url.path.endswith('/search/') else opinion())

    first = source(tmp_path, handler)
    search(first)
    expected = first.get_case('cl-101')
    first.close()
    assert TOKEN.encode() not in (tmp_path / 'source.sqlite3').read_bytes()

    def unexpected(request):
        raise AssertionError('Cached read should not call HTTP')

    second = source(tmp_path, unexpected)
    try:
        assert search(second)[0]['id'] == 'cl-101'
        assert second.get_case('cl-101')['sections'] == expected['sections']
        assert second.metrics['api_requests'] == 0
        assert second.metrics['cache_hits'] >= 2
    finally:
        second.close()


def test_unseen_results_then_pagination_and_exhausted_seen_fallback(tmp_path):
    requests = []

    def handler(request):
        requests.append(request)
        if request.url.params.get('cursor') == 'page2':
            return httpx.Response(200, json=page([case(3)]))
        next_url = str(request.url.copy_add_param('cursor', 'page2'))
        return httpx.Response(200, json=page([case(1), case(2)], next_url))

    adapter = source(tmp_path, handler)
    try:
        assert search(adapter, limit=1)[0]['id'] == 'cl-101'
        assert search(adapter, limit=1, excluded_ids={'cl-101'})[0]['id'] == 'cl-102'
        assert len(requests) == 1
        assert search(adapter, limit=1, excluded_ids={'cl-101', 'cl-102'})[0]['id'] == 'cl-103'
        assert len(requests) == 2
        fallback = search(adapter, excluded_ids={'cl-101', 'cl-102', 'cl-103'})
        assert fallback
        assert all(item['id'] in {'cl-101', 'cl-102', 'cl-103'} for item in fallback)
        assert len(requests) == 2
    finally:
        adapter.close()


@pytest.mark.parametrize('bad_case', [case(court='ca9'), case(filed='2025-01-01')])
def test_scope_mismatch_is_rejected(tmp_path, bad_case):
    adapter = source(tmp_path, lambda request: httpx.Response(200, json=page([bad_case])))
    try:
        with pytest.raises(SourceError):
            search(adapter)
    finally:
        adapter.close()


def test_all_courts_omits_court_parameter_but_preserves_dates(tmp_path):
    def handler(request):
        assert 'court' not in request.url.params
        assert request.url.params['filed_after'] == '1980-01-01'
        return httpx.Response(200, json=page([case(court='ca9')]))

    adapter = source(tmp_path, handler)
    try:
        assert search(adapter, court='all')[0]['court'] == 'ca9'
    finally:
        adapter.close()


@pytest.mark.parametrize('mutation', ['external', 'court', 'date', 'query'])
def test_unsafe_cursor_never_receives_credentials(tmp_path, mutation):
    requests = []

    def handler(request):
        requests.append(request)
        url = request.url.copy_add_param('cursor', 'next')
        if mutation == 'external':
            url = url.copy_with(host='evil.example')
        elif mutation == 'court':
            url = url.copy_set_param('court', 'ca9')
        elif mutation == 'date':
            url = url.copy_set_param('filed_after', '1800-01-01')
        else:
            url = url.copy_set_param('q', 'changed query')
        return httpx.Response(200, json=page([case()], str(url)))

    adapter = source(tmp_path, handler)
    try:
        with pytest.raises(SourceError):
            search(adapter, excluded_ids={'cl-101'})
        assert len(requests) == 1
    finally:
        adapter.close()


def test_redirect_is_rejected_without_following(tmp_path):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(302, headers={'Location': 'https://evil.example/steal'})

    adapter = source(tmp_path, handler)
    try:
        with pytest.raises(SourceError) as caught:
            search(adapter)
        assert TOKEN not in str(caught.value)
        assert len(requests) == 1
    finally:
        adapter.close()


@pytest.mark.parametrize('status', [401, 403, 429, 500])
def test_provider_failures_are_sanitized_and_retry_guidance_retained(tmp_path, status):
    adapter = source(tmp_path, lambda request: httpx.Response(status, text=TOKEN + ' provider secret',
                                                              headers={'Retry-After': '60'}))
    try:
        with pytest.raises(SourceError) as caught:
            search(adapter)
        assert caught.value.category
        assert TOKEN not in str(caught.value)
        assert 'provider secret' not in str(caught.value)
        if status == 429:
            assert caught.value.retry_after is not None
    finally:
        adapter.close()


@pytest.mark.parametrize('wrong_field', ['id', 'cluster'])
def test_wrong_opinion_identity_or_cluster_is_rejected(tmp_path, wrong_field):
    def handler(request):
        if request.url.path.endswith('/search/'):
            return httpx.Response(200, json=page())
        body = opinion()
        body[wrong_field] = 999 if wrong_field == 'id' else 'https://www.courtlistener.com/api/rest/v4/clusters/999/'
        return httpx.Response(200, json=body)

    adapter = source(tmp_path, handler)
    try:
        search(adapter)
        with pytest.raises(SourceError):
            adapter.get_case('cl-101')
    finally:
        adapter.close()


def test_round_request_budget_stops_before_extra_http(tmp_path):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=page())

    adapter = source(tmp_path, handler, request_budget=2)
    try:
        search(adapter, query='one')
        search(adapter, query='two')
        with pytest.raises(SourceError):
            search(adapter, query='three')
        assert len(requests) == 2
    finally:
        adapter.close()


def test_rate_ledger_persists_across_source_instances(tmp_path):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=page())

    first = source(tmp_path, handler)
    for query in ['one', 'two', 'three']:
        search(first, query=query)
    first.close()
    second = source(tmp_path, handler)
    try:
        for query in ['four', 'five']:
            search(second, query=query)
        with pytest.raises(SourceError) as caught:
            search(second, query='six')
        assert len(requests) == 5
        assert caught.value.retry_after is not None
    finally:
        second.close()


def test_provider_retry_after_applies_to_next_instance(tmp_path):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(429, headers={'Retry-After': '60'})

    first = source(tmp_path, handler)
    try:
        with pytest.raises(SourceError):
            search(first)
    finally:
        first.close()
    second = source(tmp_path, handler)
    try:
        with pytest.raises(SourceError) as caught:
            search(second, query='different query')
        assert caught.value.retry_after is not None
        assert len(requests) == 1
    finally:
        second.close()


def test_oversized_response_is_rejected(tmp_path):
    adapter = source(tmp_path, lambda request: httpx.Response(200, content=b'x' * (8 * 1024 * 1024 + 1)))
    try:
        with pytest.raises(SourceError):
            search(adapter)
    finally:
        adapter.close()


def test_empty_opinion_text_is_not_returned_as_evidence(tmp_path):
    def handler(request):
        if request.url.path.endswith('/search/'):
            return httpx.Response(200, json=page())
        payload = opinion()
        payload['html_with_citations'] = ''
        payload['plain_text'] = ''
        return httpx.Response(200, json=payload)

    adapter = source(tmp_path, handler)
    try:
        search(adapter)
        with pytest.raises(SourceError):
            adapter.get_case('cl-101')
    finally:
        adapter.close()


def test_short_procedural_record_is_labeled_without_fabricated_substance(tmp_path):
    def handler(request):
        if request.url.path.endswith('/search/'):
            return httpx.Response(200, json=page())
        return httpx.Response(200, json=opinion(text='<p>Synthetic short procedural order.</p>'))

    adapter = source(tmp_path, handler)
    try:
        search(adapter)
        record = adapter.get_case('cl-101')
        assert record['short_record'] is True
        assert record['text_status'] == 'short_record'
        assert record['canonical_text'] == 'Synthetic short procedural order.'
    finally:
        adapter.close()


def missing_opinion(number=1):
    record = opinion(number)
    record['html_with_citations'] = ''
    record['plain_text'] = ''
    return record


def test_missing_text_is_cached_across_instances_without_repeated_requests(tmp_path):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=page() if request.url.path.endswith('/search/')
                              else missing_opinion())

    first = source(tmp_path, handler)
    try:
        search(first)
        with pytest.raises(SourceError) as initial:
            first.get_case('cl-101')
        assert initial.value.category == 'opinion_text_missing'
        assert len(requests) == 2
    finally:
        first.close()

    def unexpected(request):
        raise AssertionError('Fresh missing-text cache must prevent repeated HTTP')

    second = source(tmp_path, unexpected)
    try:
        with pytest.raises(SourceError) as repeated:
            second.get_case('cl-101')
        assert repeated.value.category == 'opinion_text_missing'
        assert second.metrics['api_requests'] == 0
    finally:
        second.close()


def test_search_demotes_and_labels_cases_with_only_known_missing_opinions(tmp_path):
    def handler(request):
        return httpx.Response(200, json=page([case(1), case(2)])
                              if request.url.path.endswith('/search/') else missing_opinion())

    adapter = source(tmp_path, handler)
    try:
        assert [item['id'] for item in search(adapter, limit=2)] == ['cl-101', 'cl-102']
        with pytest.raises(SourceError):
            adapter.get_case('cl-101')
        # A known-unavailable unseen case must not outrank a seen usable candidate.
        repeated = search(adapter, limit=2, excluded_ids={'cl-102'})
        assert [item['id'] for item in repeated] == ['cl-102', 'cl-101']
        assert repeated[1]['text_status'] == 'unavailable'
        assert repeated[1]['unavailable_opinion_ids'] == [1001]
        assert repeated[1]['passages'] == []
        assert adapter.last_search['known_unavailable_count'] == 1
        assert adapter.metrics['api_requests'] == 2
    finally:
        adapter.close()


def test_missing_text_cache_expires_and_allows_real_refetch(tmp_path):
    first = source(tmp_path, lambda request: httpx.Response(200, json=page()
                   if request.url.path.endswith('/search/') else missing_opinion()))
    try:
        search(first)
        with pytest.raises(SourceError):
            first.get_case('cl-101')
    finally:
        first.close()

    requests = []

    def now_available(request):
        requests.append(request)
        assert request.url.path == '/api/rest/v4/opinions/1001/'
        return httpx.Response(200, json=opinion())

    second = source(tmp_path, now_available, _clock=lambda: NOW + 86401)
    try:
        refreshed = second.get_case('cl-101')
        assert refreshed['canonical_text']
        assert refreshed['sections']
        assert len(requests) == 1
        assert second.metrics['api_requests'] == 1
    finally:
        second.close()


def test_known_missing_preferred_opinion_skipped_for_labeled_alternative(tmp_path):
    first = source(tmp_path, lambda request: httpx.Response(200, json=page()
                   if request.url.path.endswith('/search/') else missing_opinion()))
    try:
        search(first)
        with pytest.raises(SourceError):
            first.get_case('cl-101')
    finally:
        first.close()

    paths = []

    def handler(request):
        paths.append(request.url.path)
        if request.url.path.endswith('/search/'):
            return httpx.Response(200, json=page([case(opinions=[
                {'id': 1001, 'type': 'lead-opinion'}, {'id': 2001, 'type': 'dissent'}])]))
        assert request.url.path == '/api/rest/v4/opinions/2001/'
        return httpx.Response(200, json=opinion(opinion_id=2001, kind='040dissent'))

    second = source(tmp_path, handler)
    try:
        found = search(second, query='synthetic alternative opinion')
        assert found[0].get('text_status') != 'unavailable'
        assert found[0]['unavailable_opinion_ids'] == [1001]
        alternative = second.get_case('cl-101')
        assert alternative['opinion_id'] == 2001
        assert alternative['opinion_scope'] == 'dissenting_opinion'
        assert all(section['opinion_id'] == 2001 and section['opinion_scope'] == 'dissenting_opinion'
                   for section in alternative['sections'])
        assert '/api/rest/v4/opinions/1001/' not in paths
        assert len(paths) == 2
    finally:
        second.close()


def test_cached_missing_text_identity_mismatch_is_rejected_without_http(tmp_path):
    first = source(tmp_path, lambda request: httpx.Response(200, json=page()
                   if request.url.path.endswith('/search/') else missing_opinion()))
    try:
        search(first)
        with pytest.raises(SourceError):
            first.get_case('cl-101')
    finally:
        first.close()

    database = sqlite3.connect(tmp_path / 'source.sqlite3')
    try:
        with database:
            body = json.loads(database.execute('SELECT body FROM source_opinions WHERE opinion_id=1001').fetchone()[0])
            body['cluster_id'] = 999
            database.execute('UPDATE source_opinions SET body=? WHERE opinion_id=1001', (json.dumps(body),))
    finally:
        database.close()

    def unexpected(request):
        raise AssertionError('Invalid cached identities must fail before HTTP')

    second = source(tmp_path, unexpected)
    try:
        with pytest.raises(SourceError) as caught:
            second.get_case('cl-101')
        assert caught.value.category == 'opinion_identity_mismatch'
        assert second.metrics['api_requests'] == 0
    finally:
        second.close()
