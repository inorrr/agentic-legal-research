#!/usr/bin/env python3
"""Real loopback HTTP smoke test using imported official text, no model calls.

Uses a disposable database; never modifies the user's workspace. Produces a safe
engineering report, not a relevance/accuracy evaluation.
"""
import csv
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:8011'


def main():
    corpus_path=ROOT/'data/corpus/index.json'
    if not corpus_path.exists(): raise SystemExit('Run scripts/import_demo_corpus.py first.')
    corpus=json.loads(corpus_path.read_text())
    scenarios=json.loads((ROOT/'examples/vehicle_search/scenarios.json').read_text())['scenarios']
    report={'mode':'real_official_pdf_local_lexical_http','model_calls':0,'scenarios':[]}
    with tempfile.TemporaryDirectory(prefix='legal-http-smoke-') as directory:
        target=Path(directory); (target/'corpus').mkdir()
        shutil.copy2(corpus_path,target/'corpus/index.json')
        env={**os.environ,'LEGAL_RESEARCH_DATA_DIR':directory}
        env.pop('OPENAI_API_KEY',None);env.pop('OPENAI_MODEL',None)
        process=None
        token=''
        def request(path,method='GET',body=None):
            headers={'X-Workspace-Token':token}
            if body is not None: headers['Content-Type']='application/json'
            req=Request(BASE+path,data=None if body is None else json.dumps(body).encode(),headers=headers,method=method)
            with urlopen(req,timeout=10) as r:
                data=r.read().decode('utf-8-sig')
                return json.loads(data) if 'json' in r.headers.get('Content-Type','') else data
        def start():
            process=subprocess.Popen([sys.executable,'-m','uvicorn','legal_research.main:app','--host','127.0.0.1','--port','8011'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            for _ in range(40):
                if process.poll() is not None: raise RuntimeError('Smoke API did not start; check port 8011 is free.')
                try: request('/api/health'); return process
                except OSError: time.sleep(.15)
            process.terminate();process.wait(timeout=5)
            raise RuntimeError('Smoke API readiness timed out')
        def stop(process):
            if process:
                process.terminate();process.wait(timeout=5)
        try:
            process=start();token=request('/api/bootstrap')['csrf_token']
            for scenario in scenarios:
                m=request('/api/matters','POST',{'title':scenario['title'],'question':scenario['research_question'],'facts':scenario['fact_pattern']})
                path='/api/matters/'+m['id']
                first=request(path+'/search','POST',{'request_id':'initial'})
                assert first['results']
                for case in first['results']:
                    original=next(c for c in corpus['cases'] if c['id']==case['id'])
                    for excerpt in case['passages']:
                        page=next(p for p in original['pages'] if p['pdf_page']==excerpt['pdf_page'])
                        assert excerpt['text'] in page['text']
                case_id=first['results'][0]['id']
                request(path+'/selections/'+case_id,'PUT',{})
                assert request(path)['feedback']=={}
                request(path+'/feedback/'+case_id,'PUT',{'relevance':'relevant','reason':scenario['optional_feedback']})
                second=request(path+'/search','POST',{})
                assert scenario['optional_feedback'] in second['query']
                exported=list(csv.DictReader(io.StringIO(request(path+'/export.csv'))))
                assert len(exported)==1 and exported[0]['id']==case_id
                assert request(path)['matter']['court']=='scotus'
                report['scenarios'].append({'id':scenario['id'],'first_results':[c['case_name'] for c in first['results']],'second_new_count':sum(c['is_new'] for c in second['results']),'export_rows':len(exported),'quotes_match_source':True})
            request('/api/settings','PUT',{'theme':'dark'})
            stop(process);process=None;process=start()
            bootstrap=request('/api/bootstrap'); token=bootstrap['csrf_token']
            assert len(bootstrap['matters'])==3 and bootstrap['settings']['theme']=='dark'
            assert len(request(path)['selections'])==1 and len(request(path)['rounds'])==2
            report['restart_persistence']='passed';report['status']='passed'
        finally: stop(process)
    output=ROOT/'data/local-workspace-smoke.json';output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
