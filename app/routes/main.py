from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def home():
    return render_template("index.html", name="Chintya")

@main_bp.route("/login")
def login():
    return render_template("auth/login.html")

@main_bp.route("/register")
def register():
    return render_template("auth/register.html")

@main_bp.route("/chat")
def chat():
    return render_template("chat/chatbot.html")
