"""Offline live-source protocol tests. No credentials or external calls."""
import copy
import hashlib
import json

from legal_research.research_agent import AgentLimits, run_research
from test_research_agent import Client, call


MATTER = {'question':'passenger purse search', 'facts':'Synthetic public facts', 'court':'all',
          'date_from':'1900-01-01', 'date_to':'2026-12-31', 'search_query':'"passenger purse"'}
CASE = {'id':'cl-101', 'case_name':'Synthetic Live Case', 'citation':'TEST ONLY', 'court':'ca9',
        'decision_date':'2024-02-01', 'source_url':'https://www.courtlistener.com/opinion/101/synthetic/',
        'summary':'', 'passages':[], 'opinion_ids':[201], 'retrieval_mode':'courtlistener'}
TEXTS = ['Synthetic background and procedural description. ' * 13,
         'Synthetic separate procedural issue and record. ' * 13,
         'Synthetic passenger purse search discussion. ' * 20,
         'Synthetic unrelated closing observations. ' * 13]
CANONICAL = ''.join(TEXTS)
HASH = hashlib.sha256(CANONICAL.encode()).hexdigest()


class LiveSource:
    source_mode = 'courtlistener'

    def __init__(self, extra=None):
        self.calls = []
        self.reads = []
        self.extra = extra or []
        self.metrics = {'api_requests':0, 'cache_hits':0}
        self.last_search = {'total':200, 'has_more':True}

    def search(self, query, **kwargs):
        self.calls.append((query, copy.deepcopy(kwargs)))
        self.metrics['api_requests'] += 1
        return [copy.deepcopy(CASE), *copy.deepcopy(self.extra)]

    def get_case(self, case_id):
        self.reads.append(case_id)
        self.metrics['api_requests'] += 1
        offset = 0
        sections = []
        for number, text in enumerate(TEXTS, start=1):
            sections.append({'section_number':number, 'text':text, 'text_start':offset,
                             'text_end':offset + len(text), 'opinion_id':201, 'opinion_scope':'020lead',
                             'source_url':CASE['source_url'], 'text_sha256':HASH,
                             'section_text_sha256':hashlib.sha256(text.encode()).hexdigest(),
                             'locator_label':f'Opinion 201, text section {number}'})
            offset += len(text)
        return {**copy.deepcopy(CASE), 'id':case_id, 'canonical_text':CANONICAL, 'sections':sections,
                'opinion_id':201, 'opinion_scope':'020lead', 'text_sha256':HASH}


def read(case_id='cl-101', numbers=None):
    return call('read_case', {'case_id':case_id, 'query':'passenger purse search', 'section_numbers':numbers or []})


def final(case_id='cl-101', evidence='cl-101:o201:s3:e1'):
    return {'status':'completed', 'output':[], 'output_text':json.dumps({'cases':[
        {'case_id':case_id, 'explanation':'A synthetic source-supported comparison.', 'evidence_ids':[evidence]}]})}


def run(responses, source=None, matter=None, feedback=None, seen=None, **kwargs):
    source = source or LiveSource()
    client = Client(responses)
    result = run_research(source, matter or MATTER, feedback or {}, seen or set(),
                          'synthetic-model', 'synthetic-key', _client=client, **kwargs)
    return result, source, client


def test_live_search_is_metadata_only_and_has_no_pdf_navigation():
    result, source, client = run([call('search_cases', {'query':'passenger purse'}),
                                 {'output':[], 'output_text':'{"cases":[]}'}])
    assert result['status'] == 'completed'
    assert source.reads == []
    payload = json.loads(client.requests[1]['input'][-1]['output'])
    assert payload['source_mode'] == 'courtlistener'
    assert payload['discovery'] == {'total':200, 'has_more':True}
    assert 'matched_pdf_pages' not in payload['cases'][0]
    assert payload['cases'][0]['text_status'] == 'not_read'
    schema = client.requests[0]['tools'][1]['parameters']
    assert set(schema['required']) == {'case_id', 'query', 'section_numbers'}


def test_live_evidence_preserves_source_identity_and_exact_canonical_offsets():
    result, source, client = run([call('search_cases', {'query':'passenger purse'}), read(), final()])
    assert result['status'] == 'completed'
    assert source.reads == ['cl-101']
    passage = result['results'][0]['passages'][0]
    assert passage['text'] == CANONICAL[passage['text_start']:passage['text_end']]
    assert passage['opinion_text_sha256'] == HASH
    assert passage['opinion_id'] == 201
    assert passage['locator_type'] == 'text_section'
    assert passage['section_number'] == 3
    assert 'pdf_page' not in passage
    assert '#page=' not in passage['source_url']
    assert result['metrics']['source_api_requests'] == 2
    assert result['source'] == 'courtlistener'
    read_output = json.loads(client.requests[2]['input'][-1]['output'])
    assert read_output['sections'][0]['section_number'] == 3
    assert all('text' not in section for section in read_output['sections'])


def test_live_specific_court_and_dates_are_independently_enforced():
    outside = {**CASE, 'id':'cl-999', 'court':'scotus'}
    source = LiveSource([outside, {**CASE, 'id':'cl-888', 'decision_date':'1800-01-01'}])
    result, source, client = run([call('search_cases', {'query':'passenger purse'}), read(), final()],
                                 source=source, matter={**MATTER, 'court':'ca9'})
    assert result['status'] == 'completed'
    payload = client.requests[1]['input'][-1]['output']
    assert 'cl-999' not in payload and 'cl-888' not in payload
    assert source.calls[0][1]['court'] == 'ca9'


def test_live_read_cannot_switch_case_or_scope_after_search():
    class ChangedSource(LiveSource):
        def get_case(self, case_id):
            return {**super().get_case(case_id), 'court':'scotus'}
    result, _, client = run([call('search_cases', {'query':'passenger purse'}), read(), final()],
                           source=ChangedSource(), matter={**MATTER, 'court':'ca9'})
    assert result['status'] == 'failed'
    assert result['results'] == []
    assert 'Invalid tool arguments' in client.requests[2]['input'][-1]['output']


def test_repeat_discovery_uses_seen_and_current_candidates_not_negative_votes():
    feedback = {'cl-adverse':{'relevance':'not_relevant', 'reason':'Synthetic factual distinction'}}
    result, source, client = run([call('search_cases', {'query':'first query'}),
                                 read(), call('search_cases', {'query':'refined query'}), final()],
                                feedback=feedback, seen={'cl-prior'})
    assert source.calls[0][1]['excluded_ids'] == {'cl-prior'}
    assert source.calls[1][1]['excluded_ids'] == {'cl-prior', 'cl-101'}
    assert 'cl-adverse' not in source.calls[1][1]['excluded_ids']
    task = json.loads(client.requests[0]['input'][0]['content'])
    assert task['feedback'] == feedback
    assert task['search_query'] == '"passenger purse"'
    assert result['results'][0]['is_new'] is True


class SourceError(Exception):
    def __init__(self, category, retry_after=None):
        super().__init__('private-provider-body synthetic-secret')
        self.category = category
        self.retry_after = retry_after


def test_rate_limit_without_evidence_is_honest_and_sanitized():
    class Limited(LiveSource):
        def search(self, *args, **kwargs):
            raise SourceError('rate', 42.2)
    result, _, _ = run([call('search_cases', {'query':'passenger purse'})], source=Limited())
    assert result['status'] == 'partial'
    assert result['results'] == []
    assert result['error'] == {'provider':'courtlistener', 'category':'rate', 'retry_after_seconds':43}
    assert 'synthetic-secret' not in json.dumps(result)


def test_source_budget_after_read_allows_validated_partial_finalization():
    class Limited(LiveSource):
        def get_case(self, case_id):
            if case_id == 'cl-202':
                raise SourceError('source_budget')
            return super().get_case(case_id)
    source = Limited([{**CASE, 'id':'cl-202'}])
    result, _, client = run([call('search_cases', {'query':'passenger purse'}), read(),
                            read('cl-202'), final()], source=source)
    assert result['status'] == 'partial'
    assert len(result['results']) == 1
    assert result['results'][0]['passages'][0]['text'] == TEXTS[2]
    assert result['error']['category'] == 'source_budget'
    assert client.requests[-1]['tool_choice'] == 'none'
    assert 'synthetic-secret' not in json.dumps(result)


def test_source_stop_cannot_be_bypassed_by_ignored_tool_choice():
    class Limited(LiveSource):
        def search(self, query, **kwargs):
            if self.calls:
                raise SourceError('rate')
            return super().search(query, **kwargs)
    result, source, client = run([call('search_cases', {'query':'first query'}), read(),
                                 call('search_cases', {'query':'second query'}),
                                 call('search_cases', {'query':'forbidden extra query'}), final()],
                                source=Limited())
    assert result['status'] == 'partial'
    assert len(source.calls) == 1
    assert client.requests[3]['tool_choice'] == 'none'
    assert client.requests[4]['tool_choice'] == 'none'


def test_unknown_source_failure_does_not_expose_raw_message_or_category():
    class Broken(LiveSource):
        def search(self, *args, **kwargs):
            raise SourceError('private-secret-category', float('nan'))
    result, _, _ = run([call('search_cases', {'query':'passenger purse'})], source=Broken())
    assert result['error'] == {'provider':'courtlistener', 'category':'source_failure'}
    assert 'private-secret' not in json.dumps(result)


def test_short_source_record_is_explicitly_labeled_to_model():
    class Short(LiveSource):
        def get_case(self, case_id):
            case = super().get_case(case_id)
            case['canonical_text'] = 'Synthetic short procedural entry.'
            case['sections'] = [{**case['sections'][0], 'text':case['canonical_text'],
                                 'text_start':0, 'text_end':len(case['canonical_text'])}]
            return case
    result, _, client = run([call('search_cases', {'query':'passenger purse'}), read(),
                            final(evidence='cl-101:o201:s1:e1')], source=Short())
    payload = json.loads(client.requests[2]['input'][-1]['output'])
    assert payload['short_record'] is True
    assert 'do not establish substantive holdings' in payload['warning']
    assert result['results'][0]['short_record'] is True


def test_missing_section_rejects_evidence_without_inventing_locator():
    result, _, _ = run([call('search_cases', {'query':'passenger purse'}), read(numbers=[999]), final()])
    assert result['status'] == 'failed'
    assert result['results'] == []


def test_live_evidence_cannot_be_reused_under_another_case_id():
    result, _, _ = run([call('search_cases', {'query':'passenger purse'}), read(), final(case_id='cl-202')],
                      source=LiveSource([{**CASE, 'id':'cl-202'}]))
    assert result['status'] == 'failed'
    assert result['results'] == []


def test_real_adapter_contract_works_with_agent_without_external_requests(tmp_path):
    import httpx
    from legal_research.courtlistener import CourtListenerSource
    from test_courtlistener_source import case, opinion, page
    requests = []

    def handler(request):
        requests.append(request.url.path)
        if request.url.path.endswith('/search/'):
            return httpx.Response(200, json=page([case(court='ca9', filed='2024-02-01')]))
        return httpx.Response(200, json=opinion(text='<p>Synthetic passenger purse source discussion. ' * 30 + '</p>'))

    adapter = CourtListenerSource(tmp_path / 'source.sqlite3', 'synthetic-only-token',
                                  _client=httpx.Client(transport=httpx.MockTransport(handler)))
    try:
        result, _, client = run([call('search_cases', {'query':'passenger purse'}), read(),
                                final(evidence='cl-101:o1001:s1:e1')], source=adapter)
        assert result['status'] == 'completed'
        assert requests == ['/api/rest/v4/search/', '/api/rest/v4/opinions/1001/']
        passage = result['results'][0]['passages'][0]
        snapshot = adapter.get_case('cl-101')
        assert passage['text'] == snapshot['canonical_text'][passage['text_start']:passage['text_end']]
        assert passage['opinion_scope'] == 'lead_opinion'
        assert json.loads(client.requests[1]['input'][-1]['output'])['discovery']['count'] == 1
    finally:
        adapter.close()


def test_actual_adapter_error_names_have_actionable_source_diagnostics():
    from legal_research.courtlistener import SourceError as AdapterError

    class Limited(LiveSource):
        def search(self, *args, **kwargs):
            raise AdapterError('rate_limited', 'Safe provider message.', 60)

    result, _, _ = run([call('search_cases', {'query':'passenger purse'})], source=Limited())
    assert result['status'] == 'partial'
    assert result['error']['category'] == 'rate_limited'
    assert result['error']['retry_after_seconds'] == 60


def test_missing_opinion_text_is_case_level_and_another_case_can_succeed():
    class MissingFirst(LiveSource):
        def get_case(self, case_id):
            if case_id == 'cl-101':
                raise SourceError('opinion_text_missing')
            return super().get_case(case_id)

    source = MissingFirst([{**CASE, 'id':'cl-202'}])
    result, _, client = run([call('search_cases', {'query':'passenger purse'}), read(),
                            read('cl-202'), final(case_id='cl-202', evidence='cl-202:o201:s3:e1')], source=source)
    assert result['status'] == 'completed'
    assert result['results'][0]['id'] == 'cl-202'
    assert 'error' not in result
    missing = json.loads(client.requests[2]['input'][-1]['output'])
    assert missing['text_status'] == 'unavailable'
    assert missing['evidence'] == []
    assert client.requests[2]['tool_choice'] == {'type':'function', 'name':'read_case'}
    assert any(action['tool'] == 'source_text_unavailable' for action in result['actions'])
    assert 'synthetic-secret' not in json.dumps(result)


def test_known_unavailable_metadata_is_exposed_and_never_refetched():
    class KnownMissing(LiveSource):
        def search(self, query, **kwargs):
            records = super().search(query, **kwargs)
            records[0]['text_status'] = 'unavailable'
            return records

    source = KnownMissing([{**CASE, 'id':'cl-202'}])
    result, _, client = run([call('search_cases', {'query':'passenger purse'}), read(),
                            read('cl-202'), final(case_id='cl-202', evidence='cl-202:o201:s3:e1')], source=source)
    assert result['status'] == 'completed'
    assert source.reads == ['cl-202']
    search_output = json.loads(client.requests[1]['input'][-1]['output'])
    assert search_output['cases'][0]['text_status'] == 'unavailable'


def test_pagination_rate_warning_allows_cached_reads_and_marks_final_partial():
    class IncompleteSearch(LiveSource):
        def search(self, query, **kwargs):
            found = super().search(query, **kwargs)
            self.last_search = {'count':200, 'has_more':True, 'error_category':'rate_limited',
                                'retry_after':45, 'stopped_reason':'private-provider-details'}
            return found

        def get_case(self, case_id):
            case = super().get_case(case_id)
            self.metrics['api_requests'] -= 1
            self.metrics['cache_hits'] += 1
            return case

    result, source, client = run([call('search_cases', {'query':'passenger purse'}), read(), final()],
                                source=IncompleteSearch())
    assert result['status'] == 'partial'
    assert len(result['results']) == 1
    assert result['error']['category'] == 'rate_limited'
    assert result['error']['retry_after_seconds'] == 45
    assert source.reads == ['cl-101']
    assert client.requests[1]['tool_choice'] == {'type':'function', 'name':'read_case'}
    assert result['metrics']['source_api_requests'] == 1
    assert result['metrics']['source_cache_hits'] == 1
    discovery = json.loads(client.requests[1]['input'][-1]['output'])['discovery']
    assert discovery['error_category'] == 'rate_limited'
    assert discovery['retry_after_seconds'] == 45
    assert 'cached' in discovery['instruction']
    assert 'private-provider-details' not in json.dumps(result) + json.dumps(client.requests)


def test_pagination_scan_limit_without_provider_error_is_still_disclosed():
    class IncompleteSearch(LiveSource):
        def search(self, query, **kwargs):
            found = super().search(query, **kwargs)
            self.last_search = {'count':200, 'has_more':True, 'stopped_reason':'untrusted arbitrary content'}
            return found

    result, _, _ = run([call('search_cases', {'query':'passenger purse'}), read(), final()],
                       source=IncompleteSearch())
    assert result['status'] == 'partial'
    assert result['error']['category'] == 'pagination_limit'
    assert 'untrusted arbitrary content' not in json.dumps(result)


def test_repeated_metadata_searches_cannot_spend_the_opinion_budget():
    # Replay the recording failure: the model tries four query variations before
    # reading. Even responses ignoring forced tool choice cannot spend that budget.
    source = LiveSource()
    source.request_budget = 4
    result, source, client = run([
        call('search_cases', {'query':f'query variation {number}'}) for number in range(4)
    ] + [read(), final()], source=source)
    assert result['status'] == 'completed'
    assert len(source.calls) == 1
    assert source.reads == ['cl-101']
    assert result['metrics']['source_api_requests'] == 2
    assert len(result['results']) == 1
    assert len([action for action in result['actions'] if action['tool'] == 'budget_guard']) == 3
    assert all(request['tool_choice'] == {'type':'function', 'name':'read_case'}
               for request in client.requests[1:5])


def test_normal_round_reserves_three_reads_and_finalizes_without_budget_error():
    source = LiveSource([{**CASE, 'id':'cl-202'}, {**CASE, 'id':'cl-303'}])
    source.request_budget = 4
    result, source, client = run([call('search_cases', {'query':'passenger purse'}),
                                 read(), read('cl-202'), read('cl-303'), final()], source=source)
    assert result['status'] == 'completed'
    assert 'error' not in result
    assert len(source.calls) == 1
    assert source.reads == ['cl-101', 'cl-202', 'cl-303']
    assert result['metrics']['source_api_requests'] == 4
    assert all(request['tool_choice'] == {'type':'function', 'name':'read_case'}
               for request in client.requests[1:4])
    assert client.requests[-1]['tool_choice'] == 'none'


def test_last_request_read_can_finalize_with_fewer_than_three_cases():
    source = LiveSource([{**CASE, 'id':'cl-202'}])
    source.request_budget = 2
    result, source, client = run([call('search_cases', {'query':'passenger purse'}), read(),
                                 call('search_cases', {'query':'ignored stop request'}), final()], source=source)
    assert result['status'] == 'completed'
    assert 'error' not in result
    assert result['metrics']['source_api_requests'] == 2
    assert len(source.calls) == 1
    assert client.requests[2]['tool_choice'] == 'none'
    assert client.requests[3]['tool_choice'] == 'none'


def test_empty_discovery_can_still_refine_its_query():
    class EmptyFirst(LiveSource):
        def search(self, query, **kwargs):
            records = super().search(query, **kwargs)
            return [] if len(self.calls) == 1 else records

    source = EmptyFirst()
    source.request_budget = 4
    result, source, client = run([call('search_cases', {'query':'no matches'}),
                                 call('search_cases', {'query':'better keywords'}), read(), final()], source=source)
    assert result['status'] == 'completed'
    assert len(source.calls) == 2
    assert client.requests[1]['tool_choice'] == 'auto'
    assert client.requests[2]['tool_choice'] == {'type':'function', 'name':'read_case'}


def test_cached_unread_opinion_remains_eligible_at_zero_source_requests():
    class CachedSecond(LiveSource):
        request_budget = 2

        def get_case(self, case_id):
            case = super().get_case(case_id)
            if case_id == 'cl-202':
                self.metrics['api_requests'] -= 1
                self.metrics['cache_hits'] += 1
            return case

    source = CachedSecond([{**CASE, 'id':'cl-202', 'text_availability':'cached'}])
    result, source, client = run([call('search_cases', {'query':'passenger purse'}), read(),
                                 read('cl-202'), final(case_id='cl-202', evidence='cl-202:o201:s3:e1')], source=source)
    assert result['status'] == 'completed'
    assert source.reads == ['cl-101', 'cl-202']
    assert result['metrics']['source_api_requests'] == 2
    assert result['metrics']['source_cache_hits'] == 1
    assert client.requests[2]['tool_choice'] == {'type':'function', 'name':'read_case'}
    assert client.requests[-1]['tool_choice'] == 'none'


def test_multiple_searches_in_one_response_cannot_bypass_read_priority():
    first = call('search_cases', {'query':'first query'})
    first['output'] += call('search_cases', {'query':'another query'})['output']
    result, source, _ = run([first, read(), final()])
    assert result['status'] == 'completed'
    assert len(source.calls) == 1
    assert source.reads == ['cl-101']
    assert any(action['tool'] == 'budget_guard' for action in result['actions'])


def test_multiple_calls_cannot_continue_retrieval_after_source_failure():
    class Limited(LiveSource):
        def search(self, query, **kwargs):
            if self.calls:
                raise SourceError('rate_limited', 30)
            return super().search(query, **kwargs)

    batch = call('search_cases', {'query':'second query hits provider limit'})
    batch['output'] += read()['output']
    result, source, _ = run([call('search_cases', {'query':'first query'}), read(), batch, final()], source=Limited())
    assert result['status'] == 'partial'
    assert result['error']['category'] == 'rate_limited'
    assert len(result['results']) == 1
    assert source.reads == ['cl-101']
    assert any(action['tool'] == 'budget_guard' for action in result['actions'])
