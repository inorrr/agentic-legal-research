#!/usr/bin/env python3
"""Opt-in, bounded OpenAI integration check on the public synthetic purse task.

Makes model requests and may incur API charges. Never prints credentials or raw
provider errors. Requires an imported corpus and confirmed local configuration.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from legal_research.config import load_local_configuration
from legal_research.corpus import Corpus
from legal_research.research_agent import run_research

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true',help='Confirm model requests for this public synthetic scenario')
    args=parser.parse_args()
    if not args.live:
        parser.error('Pass --live to run the bounded model check; no request was made.')
    config=load_local_configuration(ROOT/'.env.local',os.environ)
    if not config.get('OPENAI_API_KEY') or not config.get('OPENAI_MODEL'):
        raise SystemExit('Backend model configuration is incomplete; no request was made.')
    corpus=Corpus(ROOT/'data/corpus/index.json')
    if not corpus.count: raise SystemExit('Import the official demo corpus first; no request was made.')
    scenario=json.loads((ROOT/'examples/vehicle_search/scenarios.json').read_text())['scenarios'][1]
    matter={'question':scenario['research_question'],'facts':scenario['fact_pattern'],'court':'scotus','date_from':'1980-01-01','date_to':'2020-12-31','preferred_summary':'concise'}
    result=run_research(corpus,matter,{},set(),model=config['OPENAI_MODEL'],api_key=config['OPENAI_API_KEY'])
    audit={'checked_at':datetime.now(timezone.utc).isoformat(),'model':config['OPENAI_MODEL'],'scenario_id':scenario['id'],'source':'local_official_pdf','result':result}
    directory=ROOT/'data/live-checks';directory.mkdir(parents=True,exist_ok=True)
    report=directory/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json')
    report.write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'stop_reason':result['stop_reason'],'metrics':result['metrics'],'cases':[c['case_name'] for c in result['results']],'actions':result['actions'],'report':str(report.relative_to(ROOT))},indent=2))
    return 0 if result['status']=='completed' and result['results'] else 1


if __name__=='__main__': raise SystemExit(main())
