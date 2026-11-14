#!/bin/bash
cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit 1
if [[ ! -x .venv/bin/python ]]; then
  echo 'Complete the README setup first; the project Python environment is missing.'
  read -r -p 'Press Enter to close.'
  exit 1
fi
.venv/bin/python scripts/start_local.py --open
result=$?
if [[ "$result" -ne 0 ]]; then
  read -r -p 'Startup failed. Review the message above; press Enter to close.'
fi
exit "$result"
