"""Local workspace with explicit source selection and optional cloud analysis."""
import csv
import io
import json
import os
import secrets
import threading
import time
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .workspace import Workspace

ROOT = Path(__file__).resolve().parents[3]
ALLOWED_ORIGINS = {'http://127.0.0.1:5173', 'http://localhost:5173', 'http://127.0.0.1:8000', 'http://localhost:8000'}
COURTS = [
    {'id': 'all', 'label': 'All available U.S. courts'},
    {'id': 'scotus', 'label': 'U.S. Supreme Court'},
    *[{'id': f'ca{i}', 'label': f'Federal Court of Appeals — Circuit {i}'} for i in range(1, 12)],
    {'id': 'cadc', 'label': 'Federal Court of Appeals — D.C. Circuit'},
    {'id': 'cafc', 'label': 'Federal Court of Appeals — Federal Circuit'},
]

class MatterInput(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    question: str = Field(min_length=1, max_length=6000)
    facts: str = Field(default='', max_length=12000)
    source: Literal['local', 'courtlistener'] = 'local'
    court: str = 'scotus'
    date_from: date = date(1980,1,1)
    date_to: date = date(2020,12,31)

    @model_validator(mode='after')
    def validate_scope(self):
        if not self.title.strip() or not self.question.strip(): raise ValueError('Title and question cannot be blank')
        if self.date_from > self.date_to: raise ValueError('Start date must precede end date')
        if self.source == 'local':
            if self.court != 'scotus' or self.date_from < date(1980,1,1) or self.date_to > date(2020,12,31):
                raise ValueError('Local demo collection is Supreme Court only, 1980–2020')
        else:
            if self.court not in {item['id'] for item in COURTS}:
                raise ValueError('Choose a supported court filter')
            if self.date_from < date(1600,1,1) or self.date_to > date.today():
                raise ValueError('Choose a date range from 1600 through today')
        return self

class SearchInput(BaseModel):
    use_model: bool = False
    consent_external: bool = False
    consent_source: bool = False
    search_query: str = Field(default='', max_length=1200)
    request_id: str | None = Field(default=None, min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")

class FeedbackInput(BaseModel):
    relevance: Literal['relevant','not_relevant']
    reason: str = Field(default='', max_length=1500)

class SettingsInput(BaseModel):
    theme: Literal['light','dark'] = 'light'
    font_size: Literal['normal','large'] = 'normal'
    density: Literal['comfortable','compact'] = 'comfortable'
    preferred_summary: Literal['concise','detailed'] = 'concise'


def now(): return datetime.now(timezone.utc).isoformat()


def csv_value(value):
    text = '' if value is None else str(value)
    if text.lstrip().startswith(('=', '+', '-', '@')) or text.startswith(('\t','\r','\n')):
        return "'" + text
    return text


def create_app(data_dir: Path | None = None, ui_dir: Path | None = None, source_cache_path: Path | None = None):
    directory = data_dir or Path(os.environ.get('LEGAL_RESEARCH_DATA_DIR', ROOT / 'data')).resolve()
    token = secrets.token_urlsafe(32)
    lock = threading.Lock()

    @asynccontextmanager
    async def lifespan(app):
        app.state.workspace = Workspace(directory / 'workspace.sqlite3')
        yield

    app = FastAPI(title='Agentic Legal Case Research', version='0.2.0', lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost','127.0.0.1','testserver'])

    @app.middleware('http')
    async def local_requests(request: Request, call_next):
        origin = request.headers.get('origin')
        local_origin = str(request.base_url).rstrip('/') if request.url.hostname in {'127.0.0.1', 'localhost'} else None
        if origin and origin not in ALLOWED_ORIGINS and origin != local_origin:
            return JSONResponse({'detail':'Cross-origin access is not permitted'}, status_code=403)
        if request.headers.get('sec-fetch-site') == 'cross-site':
            return JSONResponse({'detail':'Cross-site access is not permitted'}, status_code=403)
        if request.method not in {'GET','HEAD','OPTIONS'}:
            if not secrets.compare_digest(request.headers.get('x-workspace-token',''), token):
                return JSONResponse({'detail':'Refresh the workspace to obtain a local session token'}, status_code=403)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    def store(): return app.state.workspace
    def detail(matter_id):
        result = store().detail(matter_id)
        if result is None: raise HTTPException(404,'Matter not found')
        return result
    def corpus():
        from .corpus import Corpus
        return Corpus(directory / 'corpus' / 'index.json')
    def known_case(state, case_id):
        for r in reversed(state['rounds']):
            for case in r['results']:
                if case['id'] == case_id: return case
        raise HTTPException(404, 'Case has not been retrieved in this matter')

    @app.get('/api/health')
    def health(): return {'status':'ok','stage':'local_workspace'}

    @app.get('/api/bootstrap')
    def bootstrap():
        source = corpus()
        live_ready = bool(os.environ.get('COURTLISTENER_API_TOKEN'))
        return dict(csrf_token=token,
            capabilities=dict(mode='local_workspace', agent_available=bool(os.environ.get('OPENAI_API_KEY') and os.environ.get('OPENAI_MODEL')),
                              corpus_count=source.count, courtlistener_available=live_ready),
            sources=[{'id':'courtlistener','label':'CourtListener live case search','available':live_ready},
                     {'id':'local','label':'Six-case local demo','available':source.count > 0}],
            courts=COURTS, settings=store().settings(), matters=store().matters())

    @app.get('/api/examples')
    def examples():
        return json.loads((ROOT / 'examples/vehicle_search/scenarios.json').read_text())['scenarios']

    @app.post('/api/matters',status_code=201)
    def create(body: MatterInput):
        return store().create(dict(id=str(uuid4()), created_at=now(), **body.model_dump(mode='json')))

    @app.get('/api/matters/{matter_id}')
    def get(matter_id: str): return detail(matter_id)

    @app.delete('/api/matters/{matter_id}',status_code=204)
    def delete(matter_id: str):
        # Serialize deletion with round insertion to avoid resurrecting deleted state.
        with lock:
            detail(matter_id)
            store().delete(matter_id)
        return Response(status_code=204)

    @app.post('/api/matters/{matter_id}/search')
    def search(matter_id: str, options: SearchInput):
        if not lock.acquire(blocking=False): raise HTTPException(409,'A workspace operation is in progress; try again shortly')
        live_source = None
        try:
            start = time.monotonic()
            state = detail(matter_id)
            if options.request_id:
                previous = next((r for r in state['rounds'] if r.get('request_id') == options.request_id), None)
                if previous is not None: return previous
            matter = state['matter']
            source_name = matter.get('source', 'local')
            if source_name == 'courtlistener':
                if not options.consent_source:
                    raise HTTPException(422, 'Confirm sending search queries derived from this matter and feedback to CourtListener.')
                if not os.environ.get('COURTLISTENER_API_TOKEN'):
                    raise HTTPException(409, 'CourtListener access is not configured. Run the private token setup command and restart the app.')
            if options.use_model:
                if not options.consent_external:
                    raise HTTPException(422, 'Confirm sending this matter, feedback, and passages to OpenAI before model-assisted research.')
                key, model = os.environ.get('OPENAI_API_KEY'), os.environ.get('OPENAI_MODEL')
                if not key or not model:
                    raise HTTPException(409, 'Model access is not configured; no request was made.')
            if source_name == 'courtlistener':
                from .courtlistener import CourtListenerSource
                try:
                    live_source = CourtListenerSource(source_cache_path or directory / 'courtlistener-cache.sqlite3', os.environ['COURTLISTENER_API_TOKEN'])
                except Exception:
                    raise HTTPException(409, 'The CourtListener client could not start. Check local storage and network configuration; no source request was made.') from None
                source = live_source
            else:
                source = corpus()
                if not source.count:
                    raise HTTPException(409, 'No imported opinions. Run python scripts/import_demo_corpus.py first. No external requests were made.')
            seen = {c['id'] for r in state['rounds'] for c in r['results']}
            if options.use_model:
                from .research_agent import run_research
                result = run_research(source, {**matter, 'search_query':options.search_query,
                    'preferred_summary':store().settings()['preferred_summary']}, state['feedback'], seen, model=model, api_key=key)
                result.update(source=source_name,request_id=options.request_id,id=str(uuid4()),number=len(state['rounds'])+1,created_at=now(),
                    feedback_snapshot=state['feedback'], settings_snapshot=store().settings())
                result['results'] = [{**c,'is_new':c['id'] not in seen} for c in result['results']]
                return store().round(matter_id,result)
            if source_name == 'courtlistener':
                from .source_search import run_source_search
                result = run_source_search(source, matter, state['feedback'], seen, options.search_query)
                result.update(source=source_name,request_id=options.request_id,id=str(uuid4()),number=len(state['rounds'])+1,created_at=now(),
                    feedback_snapshot=state['feedback'], settings_snapshot=store().settings())
                return store().round(matter_id,result)
            # Only explicit positive feedback reasons expand the query. Negative votes
            # must not silently exclude adverse outcomes or negate factual concepts.
            reasons = [f['reason'] for f in state['feedback'].values() if f['relevance']=='relevant' and f['reason'].strip()]
            query = (matter['question'] + ' ' + matter['facts'] + ' ' + ' '.join(reasons))[:20000]
            results = source.search(query, court=matter['court'], date_from=matter['date_from'], date_to=matter['date_to'], limit=50)
            seen = {c['id'] for r in state['rounds'] for c in r['results']}
            # Prefer unseen candidates first; votes only adjust order, never eligibility.
            def order(c):
                vote = state['feedback'].get(c['id'],{}).get('relevance')
                adjustment = {'relevant':2,'not_relevant':-2}.get(vote,0)
                return (c['id'] in seen, -(float(c.get('score',0))+adjustment))
            results.sort(key=order)
            selected = [{**c,'is_new':c['id'] not in seen} for c in results[:3]]
            new_count = sum(c['is_new'] for c in selected)
            body = dict(request_id=options.request_id,id=str(uuid4()),number=len(state['rounds'])+1, query=query, status='completed', created_at=now(),
                mode='local_corpus', source='local', feedback_snapshot=state['feedback'], settings_snapshot=store().settings(), results=selected,
                stop_reason='No new matching cases; showing previously seen matches.' if new_count==0 else f'Round budget reached: {len(selected)} cases shown; {new_count} new.',
                actions=[{'tool':'local_search','detail':f'Searched {source.count} imported opinions with fixed court/date filters.'},
                         {'tool':'feedback','detail':f"Used {len(reasons)} explicit positive reasons in query; {len(state['feedback'])} votes adjust order only. Negative reasons are retained for review, not interpreted by a model."},
                         {'tool':'source_passages','detail':'Exact PDF text excerpts; lexical matching is not legal relevance analysis.'}],
                metrics={'elapsed_ms':round((time.monotonic()-start)*1000), 'model_calls':0,'model_cost_usd':0, 'search_calls':1})
            return store().round(matter_id,body)
        finally:
            if live_source is not None:
                try:
                    live_source.close()
                except Exception:
                    pass
            lock.release()

    @app.put('/api/matters/{matter_id}/feedback/{case_id}')
    def feedback(matter_id: str,case_id: str,body: FeedbackInput):
        with lock:
            state=detail(matter_id); known_case(state,case_id)
            value={**body.model_dump(), 'updated_at':now()}
            store().set_case_state('feedback',matter_id,case_id,value)
            return value

    @app.delete('/api/matters/{matter_id}/feedback/{case_id}',status_code=204)
    def delete_feedback(matter_id: str,case_id: str):
        with lock:
            detail(matter_id); store().set_case_state('feedback',matter_id,case_id,None)
            return Response(status_code=204)

    @app.put('/api/matters/{matter_id}/selections/{case_id}')
    def select(matter_id: str,case_id: str):
        with lock:
            case=known_case(detail(matter_id),case_id)
            store().set_case_state('selections',matter_id,case_id,case)
            return case

    @app.delete('/api/matters/{matter_id}/selections/{case_id}',status_code=204)
    def unselect(matter_id: str,case_id: str):
        with lock:
            detail(matter_id); store().set_case_state('selections',matter_id,case_id,None)
            return Response(status_code=204)

    @app.get('/api/matters/{matter_id}/export.csv')
    def export(matter_id: str):
        rows=detail(matter_id)['selections']
        output=io.StringIO(newline='')
        fields=['id','case_name','citation','court','decision_date','source_url','explanation']
        writer=csv.DictWriter(output,fieldnames=fields); writer.writeheader()
        for row in rows: writer.writerow({key:csv_value(row.get(key,'')) for key in fields})
        return Response('\ufeff'+output.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="selected-cases.csv"'})

    @app.put('/api/settings')
    def settings(body: SettingsInput): return store().settings(body.model_dump())

    # Mount after API routes, from the build directory only. Never serve the
    # project root (which may contain local credentials or private matters).
    assets = ui_dir
    if assets is None and os.environ.get('LEGAL_RESEARCH_SERVE_UI') == '1':
        assets = ROOT / 'frontend' / 'dist'
    if assets is not None:
        if not (assets / 'index.html').is_file():
            raise RuntimeError('Frontend build missing. Run npm run build --prefix frontend.')
        app.mount('/', StaticFiles(directory=assets, html=True), name='workspace_ui')

    return app

app = create_app()
