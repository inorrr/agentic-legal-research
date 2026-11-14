"""Single-origin local server entry point. Configuration is loaded only on run."""
import os
import argparse
from pathlib import Path

from .config import load_local_configuration


ROOT = Path(__file__).resolve().parents[3]


def main(port=5173):
    if not 1024 <= port <= 65535:
        raise SystemExit("Choose a local port between 1024 and 65535.")
    try:
        configured = load_local_configuration(ROOT / '.env.local', os.environ)
    except ValueError as error:
        raise SystemExit(str(error)) from None
    os.environ.update(configured)
    os.environ['LEGAL_RESEARCH_SERVE_UI'] = '1'
    import uvicorn
    uvicorn.run('legal_research.main:app', host='127.0.0.1', port=port)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=5173)
    main(parser.parse_args().port)
