
from flask import Flask, render_template, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
import datetime, csv
from io import StringIO

app = Flask(__name__)
app.secret_key = "azar_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///azar.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    role = db.Column(db.String(20), default="client")

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    amount = db.Column(db.Integer)
    interest = db.Column(db.Integer)
    total = db.Column(db.Integer)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

@app.route("/", methods=["GET", "POST"])
def apply():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        amount = int(request.form["amount"])
        interest = 20000
        total = amount + interest
        loan = Loan(user_name=name, phone=phone, amount=amount, interest=interest, total=total)
        db.session.add(loan)
        db.session.commit()
        return redirect("/dashboard")
    return render_template("apply.html")

@app.route("/dashboard")
def dashboard():
    loans = Loan.query.all()
    return render_template("dashboard.html", loans=loans)

@app.route("/admin")
def admin():
    loans = Loan.query.all()
    return render_template("admin.html", loans=loans)

@app.route("/disburse/<int:id>")
def disburse(id):
    loan = Loan.query.get(id)
    loan.status = "disbursed"
    db.session.commit()
    return redirect("/admin")

@app.route("/mark_paid/<int:id>")
def mark_paid(id):
    loan = Loan.query.get(id)
    loan.status = "paid"
    db.session.commit()
    return redirect("/admin")

@app.route("/collector")
def collector():
    loans = Loan.query.all()
    return render_template("collector.html", loans=loans)

@app.route("/whatsapp")
def whatsapp():
    loans = Loan.query.all()
    return render_template("whatsapp.html", loans=loans)

@app.route("/export_csv")
def export_csv():
    loans = Loan.query.all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["Name","Phone","Amount","Interest","Total","Status","Created At"])
    for l in loans:
        cw.writerow([l.user_name,l.phone,l.amount,l.interest,l.total,l.status,l.created_at])
    output = si.getvalue()
    return send_file(StringIO(output), mimetype="text/csv", as_attachment=True, download_name="loans.csv")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()
