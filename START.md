# Quick start (Windows)

1. Activate virtualenv (PowerShell):

```powershell
.\..\expense_tracker_venv_\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:FLASK_APP='app.py'
python -m flask run
```

2. Activate virtualenv (cmd):

```cmd
..\expense_tracker_venv_\Scripts\activate.bat
python -m pip install -r requirements.txt
set FLASK_APP=app.py
python -m flask run
```

Notes:
- If your venv is located elsewhere, adjust the activation path.
- Copy `.env.example` to `.env` to persist local env vars.
