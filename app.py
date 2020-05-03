from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import os
import smtplib
import random

open("users.sqlite3", "w").close()

app = Flask(__name__)
app.secret_key = b"_5#y2L'F4Q8z\n\xec]/"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
	_id = db.Column("id", db.Integer, primary_key=True)
	username = db.Column(db.String(255), unique=True)
	email = db.Column(db.String(255), unique=True)
	password = db.Column(db.String(255))
	first = db.Column(db.String(255))
	last = db.Column(db.String(255))
	posts = db.Column(db.Integer, default=0)

	def __repr__(self):
		return f"{self.username} ({self.first} {self.last})"

class Post(db.Model):
	_id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(255))
	title = db.Column(db.String(80), nullable=False)
	body = db.Column(db.Text, nullable=False)
	pub_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	likes = db.Column(db.Integer, default=0)

code = random.randrange(1000, 5000)

@app.route("/")
def index():
	if "username" in session:
		psts = Post.query.all()
		posts = []
		delete = []
		for post in psts:
			post.pub_date = str(post.pub_date)[:19]
			if post.username == session["username"]:
				delete.append(post)
			posts.append(post)
		posts = reversed(posts)
		delete = reversed(delete)
		return render_template("index.html", posts=posts, delete=delete)
	else:
		flash("You need to login first!")
		return redirect(url_for("login"))

@app.route("/users")
def users():
	users = User.query.all()
	return render_template("users.html", users=users)

@app.route("/signup")
def signup():
	return render_template("signup.html")

@app.route("/login")
def login():
	return render_template("login.html")

@app.route("/loggingin", methods=["POST", "GET"])
def loggingin():
	username = request.form.get("username")
	password = request.form.get("password")

	found_user = User.query.filter_by(username=username).first()
	found_password = User.query.filter_by(username=username, password=password).first()

	if found_user and found_password:
		session["username"] = username
		session["email"] = User.query.filter_by(username=username).first().email
		session["password"] = password
		session["first"] = User.query.filter_by(username=username).first().first
		session["last"] = User.query.filter_by(username=username).first().last
		flash("Successfully logged in!")
		return redirect(url_for("index"))
	else:
		flash("Incorrect username or password")
		return redirect(url_for("login"))

@app.route("/signingup", methods=["POST", "GET"])
def signingup():
	username = request.form.get("username")
	email = request.form.get("email")
	password = request.form.get("password")
	first = request.form.get("first")
	last = request.form.get("last")

	found_user = User.query.filter_by(username=username).first()
	found_email = User.query.filter_by(email=email).first()

	if found_user:
		flash("This username is already taken. Try another one.")
		return redirect(url_for("signup"))
	elif found_email:
		flash("This email is already in use. Try another one.")
		return redirect(url_for("signup"))
	else:
		if username != "" and password != "" and email != "" and first != "" and last != "":
			session["username"] = username
			session["email"] = email
			session["password"] = password
			session["first"] = first
			session["last"] = last

			return redirect(url_for("verify"))
		else:
			flash("You need to fill in all fields!")
			return redirect(url_for("signup"))

body = f"{code} We need to verify your email. Please, paste this code."
message = f"""\
Subject: Email verification

{body}
"""

@app.route("/verify")
def verify():
	server = smtplib.SMTP("smtp.outlook.com", 587)
	server.starttls()
	server.login("bekhruzsniyazov@outlook.com", "microsoftpassword1")
	server.sendmail("bekhruzsniyazov@outlook.com", session["email"], message)

	return render_template("verify.html")

@app.route("/verifying", methods=["POST", "GET"])
def verifying():
	if int(request.form["code"]) == int(code):
		username = session["username"]
		email = session["email"]
		password = session["password"]
		first = session["first"]
		last = session["last"]
		usr = User(username=username, email=email, password=password, first=first, last=last)
		db.session.add(usr)
		db.session.commit()

		with open(os.path.join("templates", f"{username}.html"), "w") as f:
			f.write("{% extends \"base.html\" %}\
				{% block title %}@" + username + " on Social Media App{% endblock %}\
				{% block body %}<p style='margin-left: 5%;'>" + username + "'s email: " + email + "<br>\
				{% if not posts %}\
					<center style='maring-top: 15%; color: #d3d3d3;'><h2>This user has no posts yet...</h2></center>\
				{% else %}\
					{% for post in posts %}<a href='/{{post.title}}-post.html' class='link'>{{post.title}}</a> \
					<a href='/{{post.username}}' class='link'>@{{post.username}}</a> {{post.pub_date}} \
					{% if post in delete %}<a href='/delete-{{post.title}}' class='d'>Delete Post</a>{% endif %}<br>\
					<div style='font-size: 95%; color: gray;'>{{post.body}}<div>{% endfor %}</p>\
				{% endif %}\
				{% endblock %}")

		flash("Successfully signed up!")
		return redirect(url_for("users"))
	else:
		flash("Was not able to verify your email. Sign up again.")
		session.pop("username", None)
		session.pop("email", None)
		session.pop("password", None)
		session.pop("first", None)
		session.pop("last", None)
		return redirect(url_for("signup"))

@app.route("/add")
def add():
	if "username" in session:
		return render_template("add.html")
	else:
		flash("You need to login first!")
		return redirect(url_for("login"))

@app.route("/settings")
def settings():
	if "username" in session:
		return render_template("settings.html", username=session["username"], email=session["email"])
	else:
		flash("You need to login first!")
		return redirect(url_for("login"))

@app.route("/logout")
def logout():
	session.pop("username", None)
	session.pop("email", None)
	session.pop("password", None)
	session.pop("first", None)
	session.pop("last", None)
	flash("Successfully logged out.")
	return redirect(url_for("login"))

@app.route("/adding", methods=["POST", "GET"])
def adding():
	if session["username"]:
		post = request.form["post"]
		title = request.form["title"]
		if post != "" and title != "":
			pst = Post(username=session["username"], body=post, title=title)
			db.session.add(pst)
			db.session.commit()

			filename = f"{title}-post.html".replace(" ", "-")
			with open(os.path.join("templates", filename), "w") as file:
				file.write("{% extends \"base.html\" %}{% block title %}" + title + "{% endblock %}{% block body %}<div style='margin-left: 5%;'><h1>" + title + "</h1>" + post + "</div>{% endblock %}")

			user = User.query.filter_by(username=session["username"]).first()
			user.posts += 1
			db.session.commit()

			flash("Post added.")
			return redirect(url_for("index"))
		else:
			flash("You must fill in all fields!")
			return redirect(url_for("add"))
		
	else:
		flash("You need to login first!")
		return redirect(url_for("login"))

@app.route("/delete-<title>")
def delete(title):
	post = Post.query.filter_by(title=title.replace("-", " ")).first()
	user = User.query.filter_by(username=session["username"]).first()
	user.posts -= 1
	db.session.delete(post)
	db.session.commit()
	return redirect(url_for("index"))

@app.route("/<post>")
def post(post):
	try:
		return render_template(post.replace(" ", "-"))
	except:
		try:
			psts = []
			delete = []
			posts = Post.query.filter_by(username=session["username"]).all()
			for i in range(100):
				print(posts)
			if len(posts) == 0:
				psts.append("<h2>This user has no posts yet...</h2>")
				return render_template(f"{post}.html", posts=False, delete=[])
			else:
				if len(posts) > 5:
					for i in range(5):
						psts.append(posts[i])
						if posts[i].username == session["username"]:
							delete.append(posts[i])
				if len(posts) < 5:
					psts = posts
					for post in psts:
						if post.username == session["username"]:
							delete.append(post)
			return render_template(f"{post}.html", posts=psts, delete=delete)
		except Exception as e:
			print(e)

if __name__ == "__main__":
	db.create_all()
	app.run(debug=True)