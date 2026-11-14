#!/usr/bin/env python3
"""Privately save a CourtListener token, then run a two-request access check.

Run in your own interactive terminal. Never provide the token as an argument.
No model calls are made; live case search in the application is separate work.
"""
from __future__ import annotations

import getpass
import io
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import warnings

from dotenv.parser import parse_stream

from validate_courtlistener import probe


ROOT = Path(__file__).resolve().parents[1]
TOKEN_NAME = 'COURTLISTENER_API_TOKEN'


def save_token(path: Path, token: str) -> None:
    """Atomically change this one setting, preserving all other file contents."""
    if not token or any(character.isspace() or not character.isprintable() for character in token):
        raise ValueError('Enter a nonempty token without spaces or control characters.')
    path = Path(path)
    if path.is_symlink():
        raise ValueError('The local configuration must not be a symlink.')
    previous = None
    contents = ''
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        pass
    else:
        try:
            previous = os.fstat(descriptor)
            if not stat.S_ISREG(previous.st_mode):
                raise ValueError('The local configuration must be a regular file.')
            with os.fdopen(descriptor, encoding='utf-8', newline='') as stream:
                descriptor = None
                contents = stream.read()
        finally:
            if descriptor is not None:
                os.close(descriptor)

    escaped = token.replace('\\', '\\\\').replace("'", "\\'")
    assignment = f"{TOKEN_NAME}='{escaped}'\n"
    output = []
    replaced = False
    for binding in parse_stream(io.StringIO(contents)):
        if binding.error:
            raise ValueError('Fix the invalid local configuration before saving a token.')
        if binding.key == TOKEN_NAME:
            if not replaced:
                output.append(assignment)
            replaced = True
        else:
            output.append(binding.original.string)
    if not replaced:
        if contents and not contents.endswith('\n'):
            output.append('\n')
        output.append(assignment)

    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='',
                                         prefix='.env.courtlistener-', dir=path.parent,
                                         delete=False) as stream:
            temporary = Path(stream.name)
            os.fchmod(stream.fileno(), 0o600)
            stream.write(''.join(output))
            stream.flush()
            os.fsync(stream.fileno())
        # Do not overwrite a concurrent edit or a newly substituted symlink.
        current = path.lstat() if path.exists() or path.is_symlink() else None
        identity = lambda item: None if item is None else (item.st_dev, item.st_ino, item.st_mtime_ns, item.st_size)
        if identity(current) != identity(previous) or (current and not stat.S_ISREG(current.st_mode)):
            raise ValueError('Local configuration changed during setup; run setup again.')
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    if not sys.stdin.isatty():
        print('Run this command in your own interactive Terminal; no token was read or saved.')
        return 1
    print('This saves your token to .env.local and checks a public CourtListener search and one opinion.')
    print('At most two API requests; no OpenAI calls. The token will not appear while you paste it.')
    try:
        with warnings.catch_warnings():
            # Refuse getpass fallback to echoed input if the terminal cannot hide it.
            warnings.simplefilter('error', getpass.GetPassWarning)
            token = getpass.getpass('CourtListener API token (hidden): ')
        save_token(ROOT / '.env.local', token)
    except (KeyboardInterrupt, EOFError):
        print('\nSetup cancelled. No access check was made.')
        return 1
    except (ValueError, OSError, UnicodeError, getpass.GetPassWarning):
        print('Could not save the token. Check the input and that .env.local is a writable regular file.')
        return 1

    print('Token saved locally with owner-only permissions. Existing OpenAI settings were preserved.')
    try:
        report = probe(token, max_opinions=1)
        report_path = ROOT / 'data' / 'courtlistener-auth-check.json'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        # The probe returns metadata and fixed error categories, never raw responses.
        # Also redact the entered token if a remote metadata field reflected it.
        report_path.write_text(json.dumps(report, indent=2).replace(token, '[redacted]') + '\n', encoding='utf-8')
    except (KeyboardInterrupt, EOFError):
        print('\nToken remains saved. Access check cancelled; access is not verified.')
        return 1
    except Exception:
        print('Token remains saved. Access check or report writing failed; access is not verified.')
        return 1

    if report.get('status') == 'passed':
        print('PASSED: authenticated search and full opinion text were retrieved.')
    else:
        categories = [item.get('category', '') for item in report.get('errors', [])]
        safe = [item for item in categories if isinstance(item, str)
                and re.fullmatch(r'[a-z][a-z0-9_]{0,63}', item) and token not in item]
        print('Token remains saved. Access check did not pass: ' + (', '.join(safe) or 'access_check_failed'))
    print('Safe report: data/courtlistener-auth-check.json')
    print('This verifies source access; the app still needs its live CourtListener search integration.')
    return 0 if report.get('status') == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
