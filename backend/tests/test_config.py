"""Synthetic local-config tests; never load the project's actual env file."""
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from legal_research.config import load_local_configuration


def test_missing_file_returns_copy(tmp_path):
    original = {'EXISTING': 'synthetic'}
    loaded = load_local_configuration(tmp_path / '.env.local', original)
    assert loaded == original
    assert loaded is not original


def test_only_allowed_names_and_no_interpolation(tmp_path):
    path = tmp_path / '.env.local'
    path.write_text('OPENAI_API_KEY=synthetic-not-a-key\nOPENAI_MODEL="test-model"\n'
                    'COURTLISTENER_API_TOKEN=${HOME}\nLEGAL_RESEARCH_DATA_DIR=./data\n'
                    'PYTHONPATH=/untrusted\nVITE_API_KEY=synthetic-only\n')
    loaded = load_local_configuration(path, {'HOME': '/synthetic-home'})
    assert loaded == {'HOME': '/synthetic-home', 'OPENAI_API_KEY': 'synthetic-not-a-key',
                      'OPENAI_MODEL': 'test-model', 'COURTLISTENER_API_TOKEN': '${HOME}',
                      'LEGAL_RESEARCH_DATA_DIR': './data'}


def test_environment_wins_including_explicit_empty_value(tmp_path):
    path = tmp_path / '.env.local'
    path.write_text('OPENAI_API_KEY=synthetic-file\nOPENAI_MODEL=test-file-model\n')
    original = {'OPENAI_API_KEY': '', 'OPENAI_MODEL': 'test-env-model'}
    assert load_local_configuration(path, original) == original


def test_bare_names_ignored_and_empty_assignment_preserved(tmp_path):
    path = tmp_path / '.env.local'
    path.write_text('OPENAI_API_KEY\nOPENAI_MODEL=\n')
    assert load_local_configuration(path, {}) == {'OPENAI_MODEL': ''}


@pytest.mark.parametrize('existing_target', [True, False])
def test_symlinks_rejected_even_when_target_missing(tmp_path, existing_target):
    target = tmp_path / 'target'
    if existing_target:
        target.write_text('OPENAI_API_KEY=synthetic-not-a-key')
    link = tmp_path / '.env.local'
    link.symlink_to(target)
    with pytest.raises(ValueError, match='symlink'):
        load_local_configuration(link, {})


def test_nonregular_file_rejected(tmp_path):
    with pytest.raises(ValueError):
        load_local_configuration(tmp_path, {})


def test_server_loads_backend_config_only_when_invoked(monkeypatch, tmp_path):
    from legal_research import serve
    # No real .env path is read: this invocation substitutes a synthetic loader.
    loader = Mock(return_value={'OPENAI_MODEL': 'synthetic-test-model'})
    run = Mock()
    monkeypatch.setattr(serve, 'ROOT', tmp_path)
    monkeypatch.setattr(serve, 'load_local_configuration', loader)
    monkeypatch.setitem(sys.modules, 'uvicorn', SimpleNamespace(run=run))
    monkeypatch.setenv('OPENAI_MODEL', '')
    monkeypatch.setenv('LEGAL_RESEARCH_SERVE_UI', '')
    serve.main()
    assert loader.call_args.args[0] == tmp_path / '.env.local'
    run.assert_called_once_with('legal_research.main:app', host='127.0.0.1', port=5173)
