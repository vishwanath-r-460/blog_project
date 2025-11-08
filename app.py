from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# ---- DB path: /tmp on EB, local file when running on your PC ----
if os.path.exists("/var/app"):     # simple check that we’re on EB
    db_path = "/tmp/blog.db"
else:
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blog.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ---- Model ----
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ---- Ensure tables exist on first request (works on EB) ----
_tables_ready = False
def ensure_tables():
    global _tables_ready
    if not _tables_ready:
        with app.app_context():
            db.create_all()
        _tables_ready = True

@app.before_request
def _before_any_request():
    ensure_tables()

# ---- Routes ----
@app.route("/")
def home():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template("index.html", posts=posts)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        if title and content:
            db.session.add(Post(title=title, content=content))
            db.session.commit()
            return redirect(url_for("home"))
    return render_template("create.html")

@app.route("/post/<int:post_id>")
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("post_detail.html", post=post)

@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
def edit(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == "POST":
        post.title = request.form.get("title")
        post.content = request.form.get("content")
        db.session.commit()
        return redirect(url_for("post_detail", post_id=post.id))
    return render_template("edit.html", post=post)

@app.route("/delete/<int:post_id>", methods=["POST"])
def delete(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("home"))

# WSGI entrypoint for Gunicorn
application = app
