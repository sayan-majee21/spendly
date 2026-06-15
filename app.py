from flask import Flask, render_template, request, redirect, url_for, flash, session
from database.db import init_db, seed_db, create_user, get_user_by_email
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "dev-secret-key" # Required for flash messages

# Initialize database
with app.app_context():
    init_db()
    seed_db()

# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        # Basic validation
        if not name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")

        # Create user
        success = create_user(name, email, password)
        if success:
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("Email already registered.", "error")
            return render_template("register.html")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = get_user_by_email(email)

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("profile"))
        else:
            flash("Invalid email or password.", "error")
            return render_template("login.html")

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        flash("Please log in to view your profile.", "error")
        return redirect(url_for("login"))

    # Hardcoded mock data for Step 4
    user_data = {
        "name": session.get("user_name", "User"),
        "email": "user@example.com",
        "member_since": "June 2026",
        "initials": "U"
    }
    
    # Extract initials from name
    if "user_name" in session:
        names = session["user_name"].split()
        if len(names) >= 2:
            user_data["initials"] = (names[0][0] + names[-1][0]).upper()
        elif names:
            user_data["initials"] = names[0][0].upper()

    stats = {
        "total_spent": "₹14,250",
        "count": 24,
        "top_category": "Food & Dining"
    }

    transactions = [
        {"date": "2026-06-15", "desc": "Organic Groceries", "category": "Food", "amount": "₹2,400"},
        {"date": "2026-06-14", "desc": "Gas Station", "category": "Transport", "amount": "₹3,500"},
        {"date": "2026-06-12", "desc": "Netflix Subscription", "category": "Entertainment", "amount": "₹499"},
        {"date": "2026-06-10", "desc": "Starbucks Coffee", "category": "Food", "amount": "₹350"},
        {"date": "2026-06-08", "desc": "Gym Membership", "category": "Health", "amount": "₹2,000"}
    ]

    categories = [
        {"name": "Food", "amount": "₹5,200", "percent": 36, "class": "food"},
        {"name": "Transport", "amount": "₹4,100", "percent": 29, "class": "transport"},
        {"name": "Health", "amount": "₹3,000", "percent": 21, "class": "health"},
        {"name": "Entertainment", "amount": "₹1,950", "percent": 14, "class": "entertainment"}
    ]

    return render_template("profile.html", 
                           user=user_data, 
                           stats=stats, 
                           transactions=transactions, 
                           categories=categories)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
