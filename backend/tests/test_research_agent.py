"""Offline protocol/evidence tests. All opinions and model responses are synthetic."""
import copy
import json
from types import SimpleNamespace

from legal_research.research_agent import AgentLimits, run_research

TEXT = 'Synthetic court passage: vehicle access must be assessed on the stated facts.'
MATTER = dict(question='vehicle access',facts='Synthetic facts',court='scotus',date_from='1980-01-01',date_to='2020-12-31')
CASE = dict(id='synthetic',case_name='Synthetic Case',citation='TEST ONLY',court='scotus',decision_date='2000-01-01',source_url='https://example.test/opinion.pdf',summary='Synthetic fixture',passages=[])

class Corpus:
    def __init__(self, extra=None):
        self.calls=[]
        self.extra=extra or []
    def search(self,query,**kwargs):
        self.calls.append((query,kwargs))
        return [copy.deepcopy(CASE),*self.extra]
    def get_case(self,case_id):
        return {**CASE,'pages':[{'pdf_page':2,'text':TEXT,'text_sha256':'synthetic-hash','opinion_scope':'unsegmented'}]}

class Client:
    def __init__(self,responses):
        self.items=iter(responses)
        self.requests=[]
        self.responses=SimpleNamespace(create=self.create)
    def create(self,**kwargs):
        self.requests.append(copy.deepcopy(kwargs))
        item=next(self.items)
        if isinstance(item,Exception): raise item
        return item

def call(name,args):
    return {'status':'completed','output':[{'type':'function_call','name':name,'arguments':json.dumps(args),'call_id':f'{name}-id'}], 'usage':{'input_tokens':40,'output_tokens':20}}

def final(evidence_id='synthetic:p2:e1',case_id='synthetic'):
    return {'status':'completed','output':[], 'output_text':json.dumps({'cases':[{'case_id':case_id,'explanation':'A synthetic explanation.', 'evidence_ids':[evidence_id]}]}), 'usage':{'input_tokens':80,'output_tokens':30}}

def sequence(last=None):
    return [call('search_cases',{'query':'vehicle'}),call('read_case',{'case_id':'synthetic','pdf_pages':[2]}),last or final()]

def run(client,corpus=None,**kwargs):
    return run_research(corpus or Corpus(),MATTER,{},set(),model='test-model',api_key='test-only-key',_client=client,**kwargs)

def test_tool_loop_reads_and_verifies_exact_quotes():
    source=Corpus(); client=Client(sequence())
    result=run(client,source)
    assert result['status']=='completed'
    assert result['results'][0]['passages'][0]['text']==TEXT
    assert result['results'][0]['treatment_status']=='not_checked'
    assert result['metrics']['model_calls']==3
    assert source.calls[0][1]['court']=='scotus'
    assert all(r['store'] is False and r['parallel_tool_calls'] is False for r in client.requests)
    assert all('test-only-key' not in json.dumps(r) for r in client.requests)

def test_fabricated_evidence_reference_fails_closed():
    result=run(Client(sequence(final('synthetic:p2:invented'))))
    assert result['status']=='failed'
    assert result['results']==[]

def test_search_snippets_do_not_count_as_read_evidence():
    result=run(Client([call('search_cases',{'query':'vehicle'}),final()]))
    assert result['status']=='failed'
    assert result['results']==[]

def test_tool_cannot_override_court_filter():
    source=Corpus()
    client=Client([call('search_cases',{'query':'vehicle','court':'other'}),{'output':[],'output_text':'{"cases":[]}'}])
    result=run(client,source)
    assert source.calls==[]
    assert any(a['tool']=='rejected_tool' for a in result['actions'])

def test_source_scope_is_rechecked_before_model_sees_results():
    out={**CASE,'id':'out-of-scope','court':'other'}
    client=Client(sequence())
    result=run(client,Corpus([out]))
    assert result['status']=='completed'
    tool_output=client.requests[1]['input'][-1]['output']
    assert 'out-of-scope' not in tool_output

def test_provider_exception_is_redacted():
    result=run(Client([RuntimeError('secret-key and private request text')]))
    assert result['status']=='failed'
    assert 'secret-key' not in json.dumps(result)
    assert result['metrics']['model_calls']==1

def test_tool_budget_stops_further_work():
    result=run(Client(sequence()),limits=AgentLimits(tool_calls=1))
    assert result['status']=='partial'
    assert result['metrics']['tool_calls']==1
    assert result['results']==[]

def test_final_call_disables_tools_and_model_budget_is_bounded():
    client=Client([call('search_cases',{'query':'vehicle'})])
    result=run(client,limits=AgentLimits(model_calls=1))
    assert result['status']=='partial'
    assert client.requests[0]['tool_choice']=='none'
    assert result['metrics']['model_calls']==1

def test_feedback_and_seen_ids_are_explicit_task_context():
    client=Client(sequence())
    result=run_research(Corpus(),MATTER,{'synthetic':{'relevance':'not_relevant','reason':'different facts'}},{'synthetic'},'test-model','test-only-key',_client=client)
    task=json.loads(client.requests[0]['input'][0]['content'])
    assert task['feedback']['synthetic']['reason']=='different facts'
    assert result['results'][0]['is_new'] is False
    assert result['results'][0]['id']=='synthetic'  # Negative vote is not an exclusion.

def test_observed_token_budget_prevents_another_request():
    client=Client(sequence())
    result=run(client,limits=AgentLimits(observed_token_stop=50))
    assert len(client.requests)==1
    assert result['status']=='partial'
    assert result['metrics']['input_tokens']+result['metrics']['output_tokens']==60

def test_incomplete_response_is_not_published():
    client=Client([{'status':'incomplete','output':[],'output_text':'{"cases":[]}'}])
    assert run(client)['status']=='partial'

def test_oversized_context_makes_no_request():
    client=Client([])
    result=run(client,limits=AgentLimits(context_characters=1))
    assert result['status']=='partial'
    assert client.requests==[]

def test_time_budget_expires_before_any_model_call():
    ticks=iter([0,91,91])
    client=Client([])
    result=run(client,_clock=lambda:next(ticks))
    assert result['status']=='partial'
    assert client.requests==[]

def test_invented_case_id_rejected_even_with_delivered_evidence():
    result=run(Client(sequence(final(case_id='invented'))))
    assert result['status']=='failed'
    assert result['results']==[]

def test_explicit_summary_preference_is_transmitted_without_altering_scope():
    client=Client(sequence())
    matter={**MATTER,'preferred_summary':'detailed'}
    result=run_research(Corpus(),matter,{},set(),'test-model','test-only-key',_client=client)
    task=json.loads(client.requests[0]['input'][0]['content'])
    assert task['preferred_summary']=='detailed'
    assert task['court']==MATTER['court']
    assert result['status']=='completed'

def test_local_source_runtime_failure_is_sanitized():
    class BrokenCorpus(Corpus):
        def search(self,*args,**kwargs):
            raise OSError('private local path and secret material')
    result=run(Client(sequence()),BrokenCorpus())
    assert result['status']=='failed'
    assert result['results']==[]
    assert 'private local path' not in json.dumps(result)
    assert any(action['tool']=='source_failure' for action in result['actions'])


def test_client_initialization_failure_is_a_sanitized_zero_call_round(monkeypatch):
    def fail_client(**kwargs):
        raise ImportError('private proxy URL and secret-key must not leak')
    monkeypatch.setattr('openai.OpenAI', fail_client)
    result=run_research(Corpus(),MATTER,{},set(),'test-model','test-only-key')
    assert result['status']=='failed'
    assert result['error']=={'category':'client_configuration_error'}
    assert result['metrics']['model_calls']==0
    assert result['results']==[]
    assert 'secret-key' not in json.dumps(result)
    assert 'private proxy' not in json.dumps(result)


def test_owned_client_cleanup_failure_cannot_replace_a_round_result(monkeypatch):
    client=Client(sequence())
    close_attempts=[]
    def fail_close():
        close_attempts.append(True)
        raise RuntimeError('private cleanup details')
    client.close=fail_close
    monkeypatch.setattr('openai.OpenAI', lambda **kwargs:client)
    result=run_research(Corpus(),MATTER,{},set(),'test-model','test-only-key')
    assert result['status']=='completed'
    assert close_attempts==[True]
    assert 'private cleanup' not in json.dumps(result)


def test_provider_status_categories_are_allowlisted_and_redact_messages():
    class ProviderError(Exception):
        def __init__(self,status,code):
            super().__init__('secret-key and private request body')
            self.status_code=status
            self.code=code
    cases=[
        (401,'invalid_api_key','authentication_error'),
        (403,None,'permission_error'),
        (429,'insufficient_quota','quota_exceeded'),
        (429,'rate_limit_exceeded','rate_limit'),
        (400,'unrecognized-private-code','invalid_request'),
        (404,'model_not_found','model_unavailable'),
        (503,None,'provider_error'),
    ]
    for status,code,expected in cases:
        result=run(Client([ProviderError(status,code)]))
        assert result['status']=='failed'
        assert result['error']['category']==expected
        assert result['error']['http_status']==status
        encoded=json.dumps(result)
        assert 'secret-key' not in encoded
        assert 'private request body' not in encoded
        assert 'unrecognized-private-code' not in encoded


def test_network_failure_has_safe_actionable_category():
    from openai import APIConnectionError
    import httpx
    error=APIConnectionError(message='private network details',request=httpx.Request('POST','https://api.openai.com/v1/responses'))
    result=run(Client([error]))
    assert result['error']=={'category':'network_error'}
    assert 'private network' not in json.dumps(result)


def test_unknown_non_scalar_provider_code_is_not_serialized():
    error=RuntimeError('private error')
    error.code={'secret':'private-code'}
    result=run(Client([error]))
    assert result['error']=={'category':'request_failed'}
    assert 'private-code' not in json.dumps(result)


def test_evidence_registry_returns_exact_source_slices_and_offsets():
    from legal_research.research_agent import _page_evidence
    text=('Synthetic PDF\nline-\nbreaks  and  spaces.\n\n' * 200)[:6000]
    page={'pdf_page':13,'text':text,'source_url':'https://example.test/source.pdf#page=13','opinion_scope':'unsegmented','text_sha256':'synthetic'}
    excerpts=_page_evidence('synthetic',page)
    assert 2 <= len(excerpts) <= 3
    assert ''.join(e['text'] for e in excerpts)==text[:4000]
    for excerpt in excerpts:
        assert excerpt['text']==text[excerpt['text_start']:excerpt['text_end']]
        assert excerpt['case_id']=='synthetic'
        assert excerpt['pdf_page']==13
        assert excerpt['opinion_scope']=='unsegmented'
        assert len(excerpt['text'])<=1400


def test_delivered_evidence_cannot_be_attached_to_a_different_case():
    other={**CASE,'id':'other-case'}
    class TwoCases(Corpus):
        def get_case(self,case_id):
            return {**super().get_case(case_id),'id':case_id}
    client=Client([
        call('search_cases',{'query':'vehicle'}),
        call('read_case',{'case_id':'synthetic','pdf_pages':[2]}),
        final(evidence_id='synthetic:p2:e1',case_id='other-case'),
    ])
    result=run(client,TwoCases([other]))
    assert result['status']=='failed'
    assert result['results']==[]


def test_majority_page_suggestions_and_read_evidence_reach_model():
    class SuggestedCorpus(Corpus):
        def get_case(self,case_id):
            return {**super().get_case(case_id),'majority_pinpoints':[{'pdf_page_start':2,'pdf_page_end':2}]}
    client=Client(sequence())
    result=run(client,SuggestedCorpus())
    search_output=json.loads(client.requests[1]['input'][-1]['output'])
    assert search_output['cases'][0]['majority_pdf_pages']==[2]
    read_output=json.loads(client.requests[2]['input'][-1]['output'])
    assert read_output['evidence'][0]['evidence_id']=='synthetic:p2:e1'
    assert 'text' not in read_output['pages'][0]
    assert read_output['evidence'][0]['text']==TEXT
    assert read_output['pages'][0]['truncated'] is False
    passage=result['results'][0]['passages'][0]
    assert passage['text_start']==0
    assert passage['text_end']==len(TEXT)
    assert passage['text']==TEXT
    assert passage['source_url'].endswith('#page=2')


def test_legacy_model_transcribed_quotes_are_not_accepted():
    legacy={'status':'completed','output':[], 'output_text':json.dumps({'cases':[{'case_id':'synthetic','explanation':'Synthetic explanation','quotes':[{'pdf_page':2,'text':TEXT}]}]})}
    assert run(Client(sequence(legacy)))['status']=='failed'


def test_tool_payloads_do_not_repeat_full_source_text():
    class LongCorpus(Corpus):
        def search(self,query,**kwargs):
            return [{**CASE,'explanation':'long retrieval explanation '*100,
                     'matched_terms':['vehicle']*100,
                     'passages':[{'pdf_page':2,'text':'duplicate search text '*300}]}]
        def get_case(self,case_id):
            case=super().get_case(case_id)
            case['pages'][0]['text']=TEXT*100
            return case
    client=Client(sequence())
    result=run(client,LongCorpus())
    assert result['status']=='completed'
    search=json.loads(client.requests[1]['input'][-1]['output'])['cases'][0]
    assert 'passages' not in search and 'matched_terms' not in search and 'explanation' not in search
    assert search['matched_pdf_pages']==[2]
    read=json.loads(client.requests[2]['input'][-1]['output'])
    assert all('text' not in page for page in read['pages'])
    assert sum(len(excerpt['text']) for excerpt in read['evidence'])==4000
    assert read['pages'][0]['truncated'] is True
    assert read['pages'][0]['full_text_characters']==len(TEXT)*100
    assert set(read['evidence'][0])=={'evidence_id','pdf_page','text'}
    assert result['results'][0]['passages'][0]['page_text_sha256']=='synthetic-hash'


def test_three_read_cases_force_finalization_without_extra_retrieval():
    class ThreeCases(Corpus):
        def get_case(self,case_id):
            return {**super().get_case(case_id),'id':case_id}
    source=ThreeCases([{**CASE,'id':'second'},{**CASE,'id':'third'}])
    client=Client([
        call('search_cases',{'query':'vehicle'}),
        call('read_case',{'case_id':'synthetic','pdf_pages':[2]}),
        call('read_case',{'case_id':'second','pdf_pages':[2]}),
        call('read_case',{'case_id':'third','pdf_pages':[2]}),
        final(),
    ])
    assert run(client,source)['status']=='completed'
    assert client.requests[-1]['tool_choice']=='none'
    assert 'Finalize now' in client.requests[-1]['instructions']
