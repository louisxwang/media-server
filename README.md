## Media Server — README

Overview
- Lightweight Flask-based media browser with tagging and clip generation.

Prerequisites
- Python 3.10+ and pip
- FFMPEG (required for video clipping) — install the binaries and add them to PATH.

Repository layout (important files)
- `app.py` — launcher stub (keeps `python app.py` working). Imports package app at `src/media_server`.
- `src/media_server/` — main package:
  - `app.py` — Flask routes and integration (400 lines)
  - `config.py` — Configuration and path management (60 lines)
  - `models.py` — State management and persistence (150 lines)
  - `media_handlers.py` — File operations (delete, rename, move) (130 lines)
  - `tag_handlers.py` — Tag management logic (50 lines)
  - `browse.py` — Browse, search, and filter utilities (140 lines)
- `templates/` — HTML templates served by Flask.
- `config.json` — runtime configuration (see below).
- `requirements.txt` — runtime Python dependencies.
- `tests/` — pytest test suite.
- `.github/workflows/python-ci.yml` — CI configuration (runs tests + linter).
- `ARCHITECTURE.md` — Module architecture and design.

Config: external static/media folder
- To serve media from outside the repository, edit `config.json` at repository root. Supported keys:
  - `STATIC_PATH`: filesystem path to your media/static folder (absolute recommended).
  - `MEDIA_URL`: URL prefix used in the app (default: `static`).

Example `config.json`:
```json
{
  "STATIC_PATH": "E:\\media-static",
  "MEDIA_URL": "static"
}
```

If you want to move the repo's `static/` files into the external path, move the folder and update `STATIC_PATH`. Example PowerShell (run from project root):
```powershell
Move-Item -Path .\static -Destination E:\media-static
```

Setup & run (local)
1. Create and activate venv:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
2. Install deps and run:
```powershell
pip install -U pip
pip install -r requirements.txt
python app.py
# or using uv: uv run flask --app src.media_server.app run --host 0.0.0.0 --port 5000
```
Tests & CI
- Run tests locally:
```powershell
pip install pytest
pytest -q
```
- **87 tests** covering all major modules — see [TEST_SUMMARY.md](TEST_SUMMARY.md) for detailed coverage.
- GitHub Actions workflow is included at `.github/workflows/python-ci.yml` and runs tests + `ruff` on push/PR.

Recommended next steps
- Add `pre-commit` with `black`, `isort`, and `ruff` for consistent formatting.
- Add `mypy` for gradual static typing.

Contact / Contributing
- Open an issue or PR with changes. Keep commits small and include tests for behavior changes.

---
Updated to support external media directory and CI (Feb 2026).
### Requirements
FFMPEG is needed for video clipping. Download the binaries and edit the PATH variable to include the location of the binaries.

### Setup
Under the root, run

`uv sync`

`uv run flask --app app.py --debug run --host 0.0.0.0 --port 5000`

### Launch on RPI via SSH
Steps
- ssh into the remote machine
- start tmux by typing tmux into the shell
- start the process you want inside the started tmux session
- leave/detach the tmux session by typing Ctrl+b and then d
You can now safely log off from the remote machine, your process will keep running inside tmux. When you come back again and want to check the status of your process you can use tmux attach to attach to your tmux session.

If you want to have multiple sessions running side-by-side, you should name each session using Ctrl+b and $. You can get a list of the currently running sessions using tmux list-sessions or simply tmux ls, now attach to a running session with command tmux attach-session -t "session-name".