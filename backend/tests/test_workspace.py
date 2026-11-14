"""Synthetic workspace tests, never represented as real retrieval validation."""
import csv
import io
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from legal_research.main import create_app

class FakeCorpus:
    count=4
    def __init__(self,*args): pass
    def search(self,query,court,date_from,date_to,limit=5,**kwargs):
        assert court=='scotus'
        assert date_from=='1980-01-01'
        assert date_to=='2020-12-31'
        return [{'id':f'case-{i}','case_name':'=HYPERLINK("bad")' if i==0 else f'Synthetic {i}',
            'citation':'TEST ONLY','court':court,'decision_date':'1999-01-01',
            'source_url':'https://example.org/test','summary':'Synthetic fixture',
            'passages':[{'text':'Synthetic evidence for tests only.','pdf_page':1,'source_url':'https://example.org/test','opinion_scope':'synthetic'}],
            'explanation':'Synthetic match','score':10-i} for i in range(4)]

@pytest.fixture
def client(tmp_path):
    with patch('legal_research.corpus.Corpus', FakeCorpus), TestClient(create_app(tmp_path)) as c:
        c.headers['X-Workspace-Token']=c.get('/api/bootstrap').json()['csrf_token']
        yield c


def matter(c):
    response=c.post('/api/matters',json={'title':'Synthetic task','question':'vehicle search','facts':'public synthetic facts'})
    assert response.status_code==201
    return response.json()['id']


def test_search_feedback_history_and_selection_are_independent(client):
    mid=matter(client)
    path=f'/api/matters/{mid}'
    first=client.post(path+'/search',json={}).json()
    assert len(first['results'])==3
    client.put(path+'/selections/case-0',json={}).raise_for_status()
    assert client.get(path).json()['feedback']=={}
    client.put(path+'/feedback/case-0',json={'relevance':'relevant','reason':'passenger purse'}).raise_for_status()
    second=client.post(path+'/search',json={}).json()
    assert 'passenger purse' in second['query']
    assert second['results'][0]['id']=='case-3'
    assert second['results'][0]['is_new']
    client.put(path+'/feedback/case-0',json={'relevance':'not_relevant','reason':'unfavorable outcome'}).raise_for_status()
    third=client.post(path+'/search',json={}).json()
    assert 'passenger purse' not in third['query']
    assert 'unfavorable outcome' not in third['query']
    assert third['stop_reason'].startswith('No new')
    state=client.get(path).json()
    assert state['rounds'][1]['feedback_snapshot']['case-0']['relevance']=='relevant'
    assert state['feedback']['case-0']['relevance']=='not_relevant'
    assert len(state['selections'])==1
    client.delete(path+'/feedback/case-0').raise_for_status()
    assert not client.get(path).json()['feedback']
    # No fixed round cap.
    for _ in range(8): assert client.post(path+'/search',json={}).status_code==200


def test_csv_and_matter_isolation(client):
    mid=matter(client); other=matter(client)
    client.post(f'/api/matters/{mid}/search',json={}).raise_for_status()
    assert client.put(f'/api/matters/{other}/selections/case-0',json={}).status_code==404
    client.put(f'/api/matters/{mid}/selections/case-0',json={}).raise_for_status()
    response=client.get(f'/api/matters/{mid}/export.csv')
    rows=list(csv.DictReader(io.StringIO(response.text.lstrip('\ufeff'))))
    assert len(rows)==1
    assert rows[0]['case_name'].startswith("'=")
    assert rows[0]['id']=='case-0'
    client.delete(f'/api/matters/{mid}').raise_for_status()
    assert client.get(f'/api/matters/{mid}').status_code==404
    assert client.get(f'/api/matters/{other}').status_code==200


def test_local_origin_token_and_scope_guards(client):
    assert client.post('/api/matters',json={}).status_code==422
    body={'title':'Task','question':'question'}
    assert client.post('/api/matters',json=body,headers={'Origin':'https://evil.example'}).status_code==403
    assert client.get('/api/bootstrap',headers={'Origin':'https://evil.example'}).status_code==403
    assert client.get('/api/bootstrap',headers={'Host':'evil.example'}).status_code==400
    assert client.post('/api/matters',json=body,headers={'X-Workspace-Token':'wrong'}).status_code==403
    assert client.post('/api/matters',json={**body,'court':'ca9'}).status_code==422
    assert client.post('/api/matters',json={**body,'date_from':'2020-01-01','date_to':'1999-01-01'}).status_code==422
    assert client.post('/api/matters',json={**body,'date_to':'2026-01-01'}).status_code==422


def test_restart_persistence_and_settings(tmp_path):
    with patch('legal_research.corpus.Corpus',FakeCorpus):
        with TestClient(create_app(tmp_path)) as c:
            c.headers['X-Workspace-Token']=c.get('/api/bootstrap').json()['csrf_token']
            mid=matter(c)
            c.post(f'/api/matters/{mid}/search',json={}).raise_for_status()
            c.put(f'/api/matters/{mid}/selections/case-0',json={}).raise_for_status()
            c.put('/api/settings',json={'theme':'dark','font_size':'large','density':'compact','preferred_summary':'detailed'}).raise_for_status()
        with TestClient(create_app(tmp_path)) as c:
            data=c.get('/api/bootstrap').json()
            assert data['settings']['theme']=='dark'
            state=c.get(f'/api/matters/{mid}').json()
            assert len(state['rounds'])==1
            assert len(state['selections'])==1


def test_empty_corpus_does_not_create_fake_results(client):
    mid=matter(client)
    with patch.object(FakeCorpus,'count',0):
        response=client.post(f'/api/matters/{mid}/search',json={})
    assert response.status_code==409
    assert client.get(f'/api/matters/{mid}').json()['rounds']==[]


def test_round_idempotency_and_cloud_consent(client,monkeypatch):
    mid=matter(client)
    url=f'/api/matters/{mid}/search'
    first=client.post(url,json={'request_id':'same-request'}).json()
    again=client.post(url,json={'request_id':'same-request'}).json()
    assert first['id']==again['id']
    assert len(client.get(f'/api/matters/{mid}').json()['rounds'])==1
    assert client.post(url,json={'use_model':True}).status_code==422
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    assert client.post(url,json={'use_model':True,'consent_external':True}).status_code==409


def test_cloud_round_persistence_without_network(client,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-test-not-a-key')
    monkeypatch.setenv('OPENAI_MODEL','synthetic-test-model')
    mid=matter(client)
    answer={'results':[], 'actions':[], 'query':'test', 'stop_reason':'synthetic failure', 'status':'failed', 'mode':'openai_agent','metrics':{'model_calls':0}}
    with patch('legal_research.research_agent.run_research',return_value=answer) as agent:
        response=client.post(f'/api/matters/{mid}/search',json={'use_model':True,'consent_external':True})
    assert response.status_code==200
    assert response.json()['mode']=='openai_agent'
    assert client.get(f'/api/matters/{mid}').json()['rounds'][0]['status']=='failed'
    assert agent.call_args.args[1]['preferred_summary']=='concise'
