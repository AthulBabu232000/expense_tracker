import os
from io import BytesIO
from datetime import datetime
import re
import base64
import requests
from PIL import Image

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.objectid import ObjectId

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "devkey")

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/expense_tracker_db")
client = MongoClient(MONGO_URI)
db = client.get_default_database()

# imgbb API key (optional). If not set, app will fallback to storing no image URL.
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")

# Simple categories (placeholder)
CATEGORIES = [f"cate{i}" for i in range(1, 6)]


def _normalize_objectid_str(val: str) -> str:
    """Normalize various ObjectId string forms to the 24-hex string.
    - If val is an ObjectId-like repr: ObjectId('...') -> ...
    - If val is already a plain hex string, return as-is.
    - If val is not a string, coerce to str.
    """
    if not isinstance(val, str):
        return str(val)
    m = re.match(r"ObjectId\(['\"]([0-9a-fA-F]{24})['\"]\)", val)
    if m:
        return m.group(1)
    return val


def _serialize_doc(doc: dict) -> dict:
    """Return a shallow copy of a Mongo document with ObjectIds and datetimes stringified for templates."""
    out = dict(doc)
    # stringify primary mongo ids
    if "_id" in out:
        out["_id"] = str(out.get("_id"))
    if out.get("image_url"):
        out["image_url"] = out.get("image_url")
    ts = out.get("timestamp")
    if isinstance(ts, datetime):
        out["timestamp"] = ts.strftime("%Y-%m-%d %H:%M:%S")
    return out


def make_primary_key(month: int, year: int) -> str:
    """Generate primary key as <count>_<month>_<year>, where count resets each month."""
    count = db.entries.count_documents({"month": month, "year": year}) + 1
    return f"{count}_{month}_{year}"


@app.route("/")
def index():
    return redirect(url_for("entry"))


@app.route("/entry", methods=["GET", "POST"])
def entry():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        amount = request.form.get("amount", "").strip()

        if not name or not category or not amount:
            flash("Please fill all required fields.")
            return redirect(url_for("entry"))

        try:
            amount_val = float(amount)
        except ValueError:
            flash("Amount must be a number.")
            return redirect(url_for("entry"))

        # timestamp and primary key
        now = datetime.utcnow()
        month = now.month
        year = now.year
        primary_key = make_primary_key(month, year)

        image_file = request.files.get("image")
        image_url = None
        if image_file and image_file.filename:
            try:
                # resize/compress image
                img = Image.open(image_file.stream)
                img = img.convert("RGB")
                img.thumbnail((1024, 1024))
                buf = BytesIO()
                img.save(buf, format="JPEG", quality=75, optimize=True)
                buf.seek(0)

                # upload to imgbb if API key present
                if IMGBB_API_KEY:
                    b64 = base64.b64encode(buf.read()).decode("ascii")
                    resp = requests.post("https://api.imgbb.com/1/upload", data={
                        "key": IMGBB_API_KEY,
                        "image": b64,
                    }, timeout=30)
                    if resp.ok:
                        data = resp.json().get("data", {})
                        image_url = data.get("display_url") or data.get("url")
            except Exception:
                # don't break the whole request if image processing/upload fails
                image_url = None

        doc = {
            "primary_key": primary_key,
            "name": name,
            "category": category,
            "amount": amount_val,
            "image_url": image_url,
            "timestamp": now,
            "month": month,
            "year": year,
        }

        db.entries.insert_one(doc)
        flash("Entry saved.")
        return redirect(url_for("monthly"))

    return render_template("entry_form.html", categories=CATEGORIES)





@app.route("/monthly")
def monthly():
    # optional query params: month, year
    month = request.args.get("month", type=int) or datetime.utcnow().month
    year = request.args.get("year", type=int) or datetime.utcnow().year

    entries = [_serialize_doc(e) for e in db.entries.find({"month": month, "year": year}).sort("timestamp", -1)]

    # dummy remaining per category: let's compute remaining = 10000 - sum(amount)
    remaining_by_cat = {}
    for c in CATEGORIES:
        total = sum(e.get("amount", 0) for e in entries if e.get("category") == c)
        remaining_by_cat[c] = max(0, 10000 - total)

    return render_template("monthly.html", entries=entries, month=month, year=year, remaining_by_cat=remaining_by_cat)


@app.route("/yearly")
def yearly():
    year = request.args.get("year", type=int) or datetime.utcnow().year
    pipeline = [
        {"$match": {"year": year}},
        {"$group": {"_id": "$category", "amount_spent": {"$sum": "$amount"}}},
    ]
    agg = list(db.entries.aggregate(pipeline))
    # dummy remaining: 100000 per category
    results = []
    for row in agg:
        cat = row.get("_id")
        spent = row.get("amount_spent", 0)
        results.append({"category": cat, "amount_spent": spent, "remaining": max(0, 100000 - spent)})

    return render_template("yearly.html", year=year, results=results)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == os.getenv("ADMIN_PASSWORD", "changeme"):
            session["admin"] = True
            flash("Logged in as admin.")
            return redirect(url_for("manage"))
        flash("Invalid password.")
    return render_template("login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    flash("Logged out.")
    return redirect(url_for("index"))


def admin_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)

    return wrapper


@app.route("/manage", methods=["GET", "POST"])
@admin_required
def manage():
    # filter param
    q = request.args.get("q", "").strip()
    query = {}
    if q:
        # simple search across name and category and primary_key
        query = {"$or": [{"name": {"$regex": q, "$options": "i"}}, {"category": {"$regex": q, "$options": "i"}}, {"primary_key": {"$regex": q, "$options": "i"}}]}

    entries = [_serialize_doc(e) for e in db.entries.find(query).sort("timestamp", -1)]
    return render_template("manage.html", entries=entries, q=q)


@app.route("/delete/<entry_id>", methods=["POST"])
@admin_required
def delete(entry_id):
    eid = _normalize_objectid_str(entry_id)
    db.entries.delete_one({"_id": ObjectId(eid)})
    flash("Entry deleted.")
    return redirect(url_for("manage"))


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "1")
    app.run(host="0.0.0.0", port=5000, debug=bool(int(debug)))
