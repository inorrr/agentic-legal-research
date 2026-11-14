"""Run the API with a disposable workspace and the imported real demo corpus."""
import os
from pathlib import Path
import shutil
import tempfile
import uvicorn

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='legal-research-e2e-') as temporary:
    target=Path(temporary)
    source=root/'data/corpus/index.json'
    if not source.exists(): raise SystemExit('Import the demo corpus before running browser tests.')
    (target/'corpus').mkdir()
    shutil.copy2(source,target/'corpus/index.json')
    os.environ['LEGAL_RESEARCH_DATA_DIR']=temporary
    # Browser tests never make paid calls, even on a configured developer machine.
    os.environ.pop('OPENAI_API_KEY',None)
    os.environ.pop('OPENAI_MODEL',None)
    os.environ.pop('COURTLISTENER_API_TOKEN',None)
    uvicorn.run('legal_research.main:app',host='127.0.0.1',port=8000)
