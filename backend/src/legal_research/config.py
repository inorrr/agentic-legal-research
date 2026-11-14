"""Read explicitly allowed local backend configuration without logging values."""
from __future__ import annotations

import os
from pathlib import Path
import stat
from typing import Mapping

from dotenv import dotenv_values


ALLOWED_NAMES = frozenset({
    'OPENAI_API_KEY', 'OPENAI_MODEL', 'COURTLISTENER_API_TOKEN',
    'LEGAL_RESEARCH_DATA_DIR',
})


def load_local_configuration(path: Path, environment: Mapping[str, str]) -> dict[str, str]:
    """Return a copy with allowed file values filling absent environment names.

    An explicit empty environment value still takes precedence. Interpolation is
    disabled, and arbitrary names in the file never change the child environment.
    A missing file is normal; symlinks and nonregular files are rejected.
    """
    result = dict(environment)
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Local configuration must not be a symlink.')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        return result
    except OSError:
        raise ValueError('Cannot safely open local configuration.') from None
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError('Local configuration must be a regular file.')
        # fdopen owns the descriptor after construction and closes it on exit.
        with os.fdopen(descriptor, encoding='utf-8') as stream:
            descriptor = None
            values = dotenv_values(stream=stream, interpolate=False)
    except (OSError, UnicodeError):
        raise ValueError('Cannot read local configuration.') from None
    finally:
        if descriptor is not None:
            os.close(descriptor)
    for name in ALLOWED_NAMES:
        value = values.get(name)
        if name not in result and value is not None:
            result[name] = value
    return result
