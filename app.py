
from flask import Flask, render_template, request, redirect, session, send_file
from flask_sqlalchemy import SQLAlchemy
import datetime, csv
from io import StringIO

app = Flask(__name__)
app.secret_key = "azar_super_secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///azar.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(15), unique=True)
    password = db.Column(db.String(50))
    role = db.Column(db.String(20))

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    amount = db.Column(db.Integer)
    interest = db.Column(db.Integer)
    total = db.Column(db.Integer)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

def seed_users():
    if not User.query.first():
        users = [
            User(name="Admin", phone="0700000001", password="admin123", role="admin"),
            User(name="Collector", phone="0700000002", password="collector123", role="collector"),
            User(name="Client One", phone="0700000003", password="client123", role="client"),
            User(name="Client Two", phone="0700000004", password="client123", role="client"),
        ]
        db.session.add_all(users)
        db.session.commit()

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        phone = request.form["phone"]
        password = request.form["password"]
        user = User.query.filter_by(phone=phone, password=password).first()
        if user:
            session["role"] = user.role
            session["name"] = user.name
            session["phone"] = user.phone
            if user.role == "admin":
                return redirect("/admin")
            if user.role == "collector":
                return redirect("/collector")
            return redirect("/apply")
        return "Invalid login"
    return render_template("login.html")

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        user = User(name=request.form["name"], phone=request.form["phone"], password=request.form["password"], role="client")
        db.session.add(user)
        db.session.commit()
        return redirect("/")
    return render_template("signup.html")

@app.route("/apply", methods=["GET","POST"])
def apply():
    if "phone" not in session:
        return redirect("/")
    if request.method == "POST":
        amount = int(request.form["amount"])
        interest = 20000
        total = amount + interest
        loan = Loan(user_name=session["name"], phone=session["phone"], amount=amount, interest=interest, total=total)
        db.session.add(loan)
        db.session.commit()
        return redirect("/apply")
    loans = Loan.query.filter_by(phone=session["phone"]).all()
    return render_template("apply.html", loans=loans)

@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/")
    loans = Loan.query.all()
    return render_template("admin.html", loans=loans)

@app.route("/collector")
def collector():
    if session.get("role") != "collector":
        return redirect("/")
    loans = Loan.query.filter(Loan.status!="paid").all()
    return render_template("collector.html", loans=loans)

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

@app.route("/export_csv")
def export_csv():
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["Name","Phone","Amount","Interest","Total","Status"])
    for l in Loan.query.all():
        cw.writerow([l.user_name,l.phone,l.amount,l.interest,l.total,l.status])
    return send_file(StringIO(si.getvalue()), mimetype="text/csv", as_attachment=True, download_name="loans.csv")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_users()
    app.run()
