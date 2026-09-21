from flask import Flask, request, render_template, redirect, url_for, flash
from database import init_db
from registration import register_participant
from registration import get_participants
from mailer import send_confirmation_email
app = Flask(__name__)
app.secret_key = "doi-key-nay-thanh-chuoi-bi-mat-that"

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        result = register_participant(full_name, email, phone)

        if result["success"]:
            mail_result = send_confirmation_email(email, full_name)
            flash(result["message"])
            flash(mail_result["message"])
        else:
            flash(result["message"])

        return redirect(url_for("register"))

    return render_template("register.html")

@app.route("/participants")
def participants():
    data = get_participants()
    return render_template("participants.html", participants=data)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

