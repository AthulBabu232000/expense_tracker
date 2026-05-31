# Expense Tracker (Flask)

This repository is a minimal Flask-based expense tracker scaffold backed by MongoDB.

Quick summary of the prompt used to create this project (for future reference):

User prompt:

"I have a final goal of hosting this in render.com. I need to use mongodb as the backend database. The app has four parts: Part I - form submission page (auto timestamp, name, category dropdown, amount Rs, optional image upload, submit). Part II - monthly display (tabular: name, category, amount, remaining per category [dummy]). Part III - yearly display (tabular: category, amount spent, remaining per category). Part IV - delete/edit entries requiring authentication (simple admin password). Filtering by key/category/itemname/month. Primary key format: `<count>_<month>_<year>` with count resetting monthly. Images may be stored on GitHub later."


Files of interest:
- `app.py` - main Flask app and routes
- `requirements.txt` - Python dependencies
- `templates/` - HTML templates (`entry_form.html`, `monthly.html`, `yearly.html`, `login.html`, `manage.html`)
- `.env.example` - example environment variables

Quick local run (Windows PowerShell):

```powershell
# from repository root
cd expense_tracker
# activate your venv (adjust path if venv is elsewhere)
..\expense_tracker_venv_\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
# copy env and edit values
copy .env.example .env
# set or edit MONGO_URI in .env to point to your MongoDB (see below)
python -m flask run
```

Quick local run (Windows cmd):

```cmd
cd expense_tracker
..\expense_tracker_venv_\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
copy .env.example .env
set FLASK_APP=app.py
python -m flask run
```

Environment variables (see `.env.example`):
- `MONGO_URI` — MongoDB connection string (e.g. from MongoDB Atlas or local MongoDB)
- `SECRET_KEY` — Flask secret key
- `ADMIN_PASSWORD` — simple admin password for management UI

Notes on MongoDB Atlas:
- To use MongoDB Atlas, create a free cluster at https://www.mongodb.com/cloud/atlas, create a database user, then copy the connection string and replace the `<password>` placeholder.
- Example (SRV): `mongodb+srv://user:password@cluster0.xxxxx.mongodb.net/expense_tracker_db?retryWrites=true&w=majority`

Images:
- Currently stored in MongoDB GridFS. You said images can be stored in GitHub later; switching to external storage or keeping image files in a repository requires additional workflow (recommended: store images in object storage or commit to Git in a separate process).

Next steps you can ask me to do:
- Run the app locally and demonstrate the form flow.
- Create a Git branch and commit these changes.
- Add Dockerfile / Render deploy config.

If you want me to run the install now, say "Yes, install requirements" or ask for a commit/branch step.
# expense_tracker
This is an expense tracker made using python flask 
