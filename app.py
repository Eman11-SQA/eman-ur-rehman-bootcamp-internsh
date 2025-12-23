from flask import Flask, render_template, request, redirect, flash, session
import psycopg2
from config import Config
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = "hospital_secret"

# ------------------- DB Connection -------------------
def get_db():
    return psycopg2.connect(
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        host=Config.DB_HOST
    )

# ------------------- Fill missing visit_date -------------------
def fill_missing_visit_dates():
    conn = get_db()
    cur = conn.cursor()
    # Fix missing visit_date
    cur.execute("SELECT id FROM patients WHERE visit_date IS NULL OR visit_date=''")
    rows = cur.fetchall()
    for row in rows:
        patient_id = row[0]
        visit_date_str = f"{datetime.now().strftime('%Y%m%d')}{patient_id}"
        cur.execute("UPDATE patients SET visit_date=%s WHERE id=%s", (visit_date_str, patient_id))
    # Capitalize existing names
    cur.execute("SELECT id, name FROM patients")
    rows = cur.fetchall()
    for row in rows:
        patient_id = row[0]
        name = row[1].title()  # Capitalize
        cur.execute("UPDATE patients SET name=%s WHERE id=%s", (name, patient_id))
    conn.commit()
    cur.close()
    conn.close()

# Call this once when the app starts
fill_missing_visit_dates()

# ------------------- LOGIN -------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "employee" and password == "postgres":
            session["user"] = username
            flash("Logged in successfully!", "success")
            return redirect("/patients")
        else:
            flash("Invalid credentials!", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect("/")

# ------------------- PATIENTS -------------------
@app.route("/patients", methods=["GET"])
def patients():
    if "user" not in session:
        return redirect("/")

    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Navbar search
    search = request.args.get("search", "").strip()

    conn = get_db()
    cur = conn.cursor()

    filters = []
    params = []

    if search:
        # Patient ID = exact match, Contact & visit_date = partial match
        filters.append("(CAST(id AS TEXT) = %s OR contact ILIKE %s OR visit_date ILIKE %s)")
        params.extend([search, f"%{search}%", f"%{search}%"])

    where_clause = " WHERE " + " AND ".join(filters) if filters else ""

    # Total patients count
    cur.execute(f"SELECT COUNT(*) FROM patients {where_clause}", params)
    total_patients = cur.fetchone()[0]
    total_pages = (total_patients + per_page - 1) // per_page

    # Fetch patients
    query = f"""
        SELECT id, visit_date, name, age, disease, contact, Status
        FROM patients
        {where_clause}
        ORDER BY id ASC
        LIMIT %s OFFSET %s
    """
    params.extend([per_page, (page - 1) * per_page])
    cur.execute(query, params)
    patients_list = cur.fetchall()
    conn.close()

    return render_template(
        "patients.html",
        patients=patients_list,
        page=page,
        total_pages=total_pages,
        search=search
    )


    # # Get total patients for pagination
    # cur.execute(f"SELECT COUNT(*) FROM patients {where_clause}", params)
    # total_patients = cur.fetchone()[0]
    # total_pages = (total_patients + per_page - 1) // per_page

    # # Fetch patients
    # query = f"""
    #     SELECT id, visit_date, name, age, disease, contact, Status
    #     FROM patients
    #     {where_clause}
    #     ORDER BY id ASC
    #     LIMIT %s OFFSET %s
    # """
    # params.extend([per_page, (page - 1) * per_page])
    # cur.execute(query, params)
    # patients_list = cur.fetchall()
    # conn.close()

    # return render_template("patients.html",
    #                        patients=patients_list,
    #                        page=page,
    #                        total_pages=total_pages,
    #                        search_id=search_id or "",
    #                        search_contact=search_contact or "",
    #                        search_date=search_date or "")

# ------------------- ADD PATIENT -------------------
@app.route("/add", methods=["GET", "POST"])
def add_patient():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        name = request.form["name"].title()  # Capitalize first letters
        age = request.form["age"]
        disease = request.form["disease"]
        contact = request.form["contact"]

        # Phone validation
        phone_pattern = r"^\+\d{1,3}[-\s]?\d{8,12}$"
        if not re.match(phone_pattern, contact):
            flash("Invalid phone number format! Example: +92-3001234567", "danger")
            return redirect("/add")

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO patients (name, age, disease, contact) VALUES (%s,%s,%s,%s) RETURNING id",
            (name, age, disease, contact)
        )
        patient_id = cur.fetchone()[0]

        # Add visit_date next to id, no dashes
        visit_date_str = f"{datetime.now().strftime('%Y%m%d')}{patient_id}"
        cur.execute("UPDATE patients SET visit_date=%s WHERE id=%s", (visit_date_str, patient_id))

        conn.commit()
        conn.close()
        flash("Patient added!", "success")
        return redirect("/patients")

    return render_template("add_patient.html")

# ------------------- EDIT PATIENT -------------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_patient(id):
    if "user" not in session:
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form["name"].title()  # Capitalize
        age = request.form["age"]
        disease = request.form["disease"]
        contact = request.form["contact"]

        phone_pattern = r"^\+\d{1,3}[-\s]?\d{8,12}$"
        if not re.match(phone_pattern, contact):
            flash("Invalid phone number format!", "danger")
            return redirect(f"/edit/{id}")

        cur.execute(
            "UPDATE patients SET name=%s, age=%s, disease=%s, contact=%s WHERE id=%s",
            (name, age, disease, contact, id)
        )
        conn.commit()
        conn.close()
        flash("Patient updated!", "info")
        return redirect("/patients")

    cur.execute("SELECT * FROM patients WHERE id=%s", (id,))
    patient = cur.fetchone()
    conn.close()
    return render_template("edit_patient.html", patient=patient)

# ------------------- DELETE PATIENT -------------------
@app.route("/delete/<int:id>")
def delete_patient(id):
    if "user" not in session:
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM patients WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    flash("Patient deleted!", "danger")
    return redirect("/patients")

# ------------------- RUN APP -------------------
if __name__ == "__main__":
    app.run(debug=True)
