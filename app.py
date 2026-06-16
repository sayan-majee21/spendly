import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from flask import Flask, render_template, request, redirect, url_for, flash, session
from database.db import (
    init_db, seed_db, create_user, get_user_by_email,
    get_user_by_id, get_user_expenses, get_user_stats, get_category_breakdown
)
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
    """Step 5: Render the profile page with real database data."""
    if not session.get("user_id"):
        flash("Please log in to view your profile.", "error")
        return redirect(url_for("login"))

    from datetime import datetime
    
    user_id = session["user_id"]
    user_record = get_user_by_id(user_id)

    # Format user data
    user_data = {
        "name": user_record["name"],
        "email": user_record["email"],
        "initials": "U"
    }

    # Format member_since
    try:
        dt = datetime.strptime(user_record["created_at"], "%Y-%m-%d %H:%M:%S")
        user_data["member_since"] = dt.strftime("%B %Y")
    except (ValueError, TypeError):
        user_data["member_since"] = "Unknown"

    # Extract initials from name
    names = user_data["name"].split()
    if len(names) >= 2:
        user_data["initials"] = (names[0][0] + names[-1][0]).upper()
    elif names:
        user_data["initials"] = names[0][0].upper()

    # Get and format stats
    raw_stats = get_user_stats(user_id)
    stats = {
        "total_spent": f"₹{raw_stats['total_spent']:,.2f}",
        "count": raw_stats['count'],
        "top_category": raw_stats['top_category'] or "None"
    }

    # Get and format transactions
    raw_expenses = get_user_expenses(user_id)
    transactions = []
    for exp in raw_expenses:
        transactions.append({
            "date": exp["date"],
            "desc": exp["description"],
            "category": exp["category"],
            "amount": f"₹{exp['amount']:,.2f}"
        })

    # Get and format categories
    categories = get_category_breakdown(user_id)
    for cat in categories:
        cat["amount"] = f"₹{cat['amount']:,.2f}"

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
