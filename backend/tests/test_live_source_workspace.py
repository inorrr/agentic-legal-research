"""Live-source route checks with synthetic adapters; never sends credentials."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from legal_research.main import create_app
from legal_research.courtlistener import SourceError


class FakeSource:
    source_mode = 'courtlistener'
    instances = []
    failure_after = None

    def __init__(self, *args, **kwargs):
        self.metrics = {'api_requests':0, 'cache_hits':0}
        self.last_search = {'count':30, 'has_more':True}
        self.calls = []
        self.closed = False
        self.reads = 0
        self.instances.append(self)

    def search(self, query, court, date_from, date_to, excluded_ids=None, limit=5):
        self.calls.append((query, court, date_from, date_to, set(excluded_ids or [])))
        cases = [{'id':f'cl-{i}', 'case_name':f'Synthetic case {i}', 'citation':'TEST ONLY',
                  'court':'ca9', 'decision_date':'2025-01-02', 'source_url':f'https://www.courtlistener.com/opinion/{i}/test/',
                  'summary':'', 'passages':[], 'score':10-i, 'retrieval_mode':'courtlistener'} for i in range(1,8)]
        return sorted(cases, key=lambda c: c['id'] in set(excluded_ids or []))[:limit]

    def get_case(self, case_id):
        if self.failure_after is not None and self.reads >= self.failure_after:
            raise SourceError('rate_limited', 'Source allowance exhausted.', 42)
        self.reads += 1
        text = 'Synthetic vehicle passenger evidence for route tests. ' * 15
        case = next(c for c in self.search('synthetic', 'all', '1900-01-01', '2026-01-01') if c['id']==case_id)
        return {**case, 'canonical_text':text, 'text_sha256':'synthetic-hash',
                'sections':[{'section_number':1, 'text':text, 'text_start':0, 'text_end':len(text),
                    'source_url':case['source_url'], 'opinion_id':123, 'opinion_scope':'lead_opinion'}]}

    def close(self):
        self.closed = True


@pytest.fixture
def live_client(tmp_path, monkeypatch):
    monkeypatch.setenv('COURTLISTENER_API_TOKEN', 'synthetic-only-not-a-token')
    FakeSource.instances = []
    FakeSource.failure_after = None
    with patch('legal_research.courtlistener.CourtListenerSource', FakeSource), TestClient(create_app(tmp_path)) as client:
        client.headers['X-Workspace-Token'] = client.get('/api/bootstrap').json()['csrf_token']
        yield client


def matter(client, **changes):
    result = client.post('/api/matters', json={'title':'Synthetic live matter', 'question':'passenger vehicle search',
        'source':'courtlistener', 'court':'all', 'date_from':'1900-01-01', 'date_to':'2026-01-01', **changes})
    assert result.status_code == 201
    return result.json()['id']


def test_live_source_runs_without_local_corpus_and_preserves_state(live_client):
    bootstrap = live_client.get('/api/bootstrap').json()
    assert bootstrap['capabilities']['corpus_count'] == 0
    assert bootstrap['capabilities']['courtlistener_available'] is True
    assert any(item['id']=='all' for item in bootstrap['courts'])
    mid = matter(live_client)
    path = f'/api/matters/{mid}'
    first = live_client.post(path+'/search', json={'consent_source':True, 'search_query':'passenger AND vehicle', 'request_id':'one'}).json()
    assert first['status'] == 'completed'
    assert first['mode'] == 'courtlistener_search'
    assert first['source'] == 'courtlistener'
    assert len(first['results']) == 3
    assert first['query'] == 'passenger AND vehicle'
    passage = first['results'][0]['passages'][0]
    assert 'pdf_page' not in passage
    assert passage['opinion_id'] == 123
    assert passage['text_end']-passage['text_start'] == len(passage['text'])
    assert FakeSource.instances[-1].closed
    count = len(FakeSource.instances)
    repeat = live_client.post(path+'/search', json={'request_id':'one'}).json()
    assert repeat['id'] == first['id']
    assert len(FakeSource.instances)==count
    live_client.put(path+'/selections/cl-1', json={}).raise_for_status()
    live_client.put(path+'/feedback/cl-1', json={'relevance':'relevant','reason':'container distinction'}).raise_for_status()
    second = live_client.post(path+'/search', json={'consent_source':True}).json()
    assert 'container' in second['query']
    assert all(case['is_new'] for case in second['results'])
    assert first['results'][0]['id'] not in {case['id'] for case in second['results']}
    assert second['feedback_snapshot']['cl-1']['reason']=='container distinction'
    assert 'cl-1' in live_client.get(path+'/export.csv').text
    assert len(live_client.get(path).json()['selections'])==1


def test_source_consent_and_configuration_checked_before_any_requests(live_client, monkeypatch):
    mid = matter(live_client)
    path = f'/api/matters/{mid}/search'
    assert live_client.post(path, json={}).status_code == 422
    assert not FakeSource.instances
    monkeypatch.delenv('COURTLISTENER_API_TOKEN')
    assert live_client.post(path, json={'consent_source':True}).status_code == 409
    assert not FakeSource.instances


def test_provider_rate_failure_retains_partial_results_and_retry(live_client):
    FakeSource.failure_after = 1
    mid = matter(live_client)
    result = live_client.post(f'/api/matters/{mid}/search', json={'consent_source':True}).json()
    assert result['status']=='partial'
    assert len(result['results'])==1
    assert result['error']=={'provider':'courtlistener','category':'rate_limited','retry_after':42}
    assert FakeSource.instances[-1].closed


def test_live_filters_and_model_consent_are_independent(live_client, monkeypatch):
    mid = matter(live_client, court='ca9')
    monkeypatch.setenv('OPENAI_API_KEY', 'synthetic-model-key')
    monkeypatch.setenv('OPENAI_MODEL', 'test-model')
    path=f'/api/matters/{mid}/search'
    assert live_client.post(path, json={'consent_source':True,'use_model':True}).status_code==422
    assert not FakeSource.instances
    answer={'results':[], 'actions':[], 'query':'synthetic','stop_reason':'test', 'status':'completed','mode':'openai_agent','metrics':{}}
    with patch('legal_research.research_agent.run_research', return_value=answer) as agent:
        result=live_client.post(path,json={'consent_source':True,'consent_external':True,'use_model':True,'search_query':'explicit query'})
    assert result.status_code==200
    assert agent.call_args.args[1]['court']=='ca9'
    assert agent.call_args.args[1]['search_query']=='explicit query'
    assert FakeSource.instances[-1].closed


def test_unrecognized_filters_are_rejected(live_client):
    response=live_client.post('/api/matters',json={'title':'Test','question':'Question','source':'courtlistener','court':'fake'})
    assert response.status_code==422
    response=live_client.post('/api/matters',json={'title':'Test','question':'Question','source':'courtlistener','date_from':'1500-01-01'})
    assert response.status_code==422


def test_long_question_retains_feedback_terms():
    from legal_research.source_search import search_terms
    query = search_terms({'question':' '.join(f'concept{n}' for n in range(30))},
        {'cl-1':{'relevance':'relevant','reason':'passenger purse belongings'}})
    assert 'passenger' in query and 'purse' in query
    assert query.count(' OR ')==17


def test_missing_text_does_not_block_remaining_candidates():
    from legal_research.source_search import run_source_search
    class MissingFirst(FakeSource):
        def get_case(self, case_id):
            if case_id=='cl-1':
                raise SourceError('opinion_text_missing','No usable text.')
            return super().get_case(case_id)
    source=MissingFirst()
    source.failure_after=None
    result=run_source_search(source, {'question':'passenger vehicle', 'court':'all','date_from':'1900-01-01','date_to':'2026-01-01'}, {}, set())
    assert result['status']=='completed'
    assert [c['id'] for c in result['results']]==['cl-2','cl-3','cl-4']
    assert any(action['tool']=='unavailable_text' for action in result['actions'])


def test_pagination_limit_surfaces_with_cached_results():
    from legal_research.source_search import run_source_search
    source=FakeSource()
    source.failure_after=None
    source.last_search.update(stopped_reason='Pagination paused.',error_category='rate_limited',retry_after=30)
    result=run_source_search(source, {'question':'passenger vehicle', 'court':'all','date_from':'1900-01-01','date_to':'2026-01-01'}, {}, set())
    assert result['status']=='partial'
    assert len(result['results'])==3
    assert 'Pagination paused' in result['stop_reason']
    assert result['error']['retry_after']==30
