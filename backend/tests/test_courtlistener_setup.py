"""Credential setup tests use only temporary files and synthetic credentials."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
from types import SimpleNamespace
from unittest.mock import Mock

from dotenv import dotenv_values
import pytest


SCRIPTS = Path(__file__).resolve().parents[2] / 'scripts'
spec = importlib.util.spec_from_file_location('validate_courtlistener', SCRIPTS / 'validate_courtlistener.py')
probe_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe_module)
sys.modules.setdefault('validate_courtlistener', probe_module)
spec = importlib.util.spec_from_file_location('courtlistener_setup', SCRIPTS / 'configure_courtlistener.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


def test_preserves_other_credentials_comments_and_literal_values(tmp_path):
    path = tmp_path / '.env.local'
    original = '# Local settings\nOPENAI_API_KEY=synthetic-openai\nOPENAI_MODEL="test-model"\nOTHER=${HOME}'
    path.write_text(original)
    setup.save_token(path, "synthetic-'token\\value")
    assert path.read_text().startswith(original + '\n')
    values = dotenv_values(path, interpolate=False)
    assert values == {'OPENAI_API_KEY': 'synthetic-openai', 'OPENAI_MODEL': 'test-model',
                      'OTHER': '${HOME}', 'COURTLISTENER_API_TOKEN': "synthetic-'token\\value"}
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert list(tmp_path.glob('.env.courtlistener-*')) == []


def test_replaces_existing_token_without_duplicating_and_supports_new_file(tmp_path):
    path = tmp_path / '.env.local'
    setup.save_token(path, 'synthetic-old')
    with path.open('a') as stream:
        stream.write('export COURTLISTENER_API_TOKEN="synthetic-duplicate"\n')
    setup.save_token(path, 'synthetic-new')
    assert path.read_text().count('COURTLISTENER_API_TOKEN') == 1
    assert dotenv_values(path)['COURTLISTENER_API_TOKEN'] == 'synthetic-new'
    assert 'synthetic-old' not in path.read_text()


@pytest.mark.parametrize('token', ['', ' ', ' token', 'token ', 'two words', 'token\nvalue', 'token\tvalue', 'token\x00value', 'token\x1bvalue'])
def test_invalid_token_does_not_modify_configuration(tmp_path, token):
    path = tmp_path / '.env.local'
    path.write_text('OPENAI_API_KEY=synthetic-existing\n')
    before = path.read_bytes()
    with pytest.raises(ValueError):
        setup.save_token(path, token)
    assert path.read_bytes() == before
    assert list(tmp_path.glob('.env.courtlistener-*')) == []


@pytest.mark.parametrize('exists', [False, True])
def test_symlink_rejected_without_changing_target(tmp_path, exists):
    target = tmp_path / 'target'
    if exists:
        target.write_text('OPENAI_API_KEY=synthetic-existing\n')
    link = tmp_path / '.env.local'
    link.symlink_to(target)
    with pytest.raises(ValueError):
        setup.save_token(link, 'synthetic-token')
    assert link.is_symlink()
    assert target.exists() == exists
    if exists:
        assert target.read_text() == 'OPENAI_API_KEY=synthetic-existing\n'


def test_nonregular_destination_rejected(tmp_path):
    directory = tmp_path / '.env.local'
    directory.mkdir()
    with pytest.raises((ValueError, OSError)):
        setup.save_token(directory, 'synthetic-token')
    assert directory.is_dir()


def test_failed_replace_preserves_original_and_cleans_temporary(tmp_path, monkeypatch):
    path = tmp_path / '.env.local'
    path.write_text('OPENAI_API_KEY=synthetic-existing\n')
    monkeypatch.setattr(setup.os, 'replace', Mock(side_effect=OSError('synthetic-error')))
    with pytest.raises(OSError):
        setup.save_token(path, 'synthetic-token')
    assert path.read_text() == 'OPENAI_API_KEY=synthetic-existing\n'
    assert list(tmp_path.glob('.env.courtlistener-*')) == []


def interactive(monkeypatch, tmp_path):
    monkeypatch.setattr(setup, 'ROOT', tmp_path)
    monkeypatch.setattr(setup.sys, 'stdin', SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr(setup.getpass, 'getpass', Mock(return_value='synthetic-private-token'))


def test_setup_runs_bounded_probe_and_prints_no_credentials(tmp_path, monkeypatch, capsys):
    interactive(monkeypatch, tmp_path)
    probe = Mock(return_value={'status': 'passed', 'errors': [], 'cases': [{'name': 'Synthetic case'}]})
    monkeypatch.setattr(setup, 'probe', probe)
    assert setup.main() == 0
    probe.assert_called_once_with('synthetic-private-token', max_opinions=1)
    assert dotenv_values(tmp_path / '.env.local')['COURTLISTENER_API_TOKEN'] == 'synthetic-private-token'
    report = (tmp_path / 'data/courtlistener-auth-check.json').read_text()
    output = capsys.readouterr().out
    assert 'PASSED' in output
    assert 'synthetic-private-token' not in output + report


def test_access_failure_keeps_saved_token_and_reports_safe_status(tmp_path, monkeypatch, capsys):
    interactive(monkeypatch, tmp_path)
    monkeypatch.setattr(setup, 'probe', Mock(return_value={'status': 'blocked', 'errors': [
        {'stage': 'search', 'category': 'authentication_required_or_invalid'}]}))
    assert setup.main() == 1
    output = capsys.readouterr().out
    assert 'Token remains saved' in output
    assert 'authentication_required_or_invalid' in output
    assert 'synthetic-private-token' not in output
    assert (tmp_path / '.env.local').is_file()


def test_unexpected_probe_exception_never_prints_raw_details(tmp_path, monkeypatch, capsys):
    interactive(monkeypatch, tmp_path)
    monkeypatch.setattr(setup, 'probe', Mock(side_effect=RuntimeError('synthetic-private-token provider body')))
    assert setup.main() == 1
    output = capsys.readouterr().out
    assert 'Token remains saved' in output
    assert 'synthetic-private-token' not in output
    assert 'provider body' not in output


def test_requires_terminal_before_reading_or_saving_token(tmp_path, monkeypatch, capsys):
    interactive(monkeypatch, tmp_path)
    monkeypatch.setattr(setup.sys, 'stdin', SimpleNamespace(isatty=lambda: False))
    probe = Mock()
    monkeypatch.setattr(setup, 'probe', probe)
    assert setup.main() == 1
    setup.getpass.getpass.assert_not_called()
    probe.assert_not_called()
    assert not (tmp_path / '.env.local').exists()


@pytest.mark.parametrize('error', [KeyboardInterrupt, EOFError])
def test_cancelled_prompt_does_not_save_or_probe(tmp_path, monkeypatch, error, capsys):
    interactive(monkeypatch, tmp_path)
    monkeypatch.setattr(setup.getpass, 'getpass', Mock(side_effect=error))
    probe = Mock()
    monkeypatch.setattr(setup, 'probe', probe)
    assert setup.main() == 1
    assert 'cancelled' in capsys.readouterr().out
    probe.assert_not_called()
    assert not (tmp_path / '.env.local').exists()
