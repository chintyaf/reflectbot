from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html", name="Chintya")

@app.route("/login")
def login():
    return render_template("auth/login.html")

@app.route("/register")
def register():
    return render_template("auth/register.html")

@app.route("/chat")
def chat():
    return render_template("chat/chatbot.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)