import psycopg2
from faker import Faker
from config import Config
from datetime import datetime
import random

fake = Faker()

conn = psycopg2.connect(
    dbname=Config.DB_NAME,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    host=Config.DB_HOST
)
cur = conn.cursor()

for i in range(1000):
    name = fake.name().title()
    first_name = name.split()[0]
    age = fake.random_int(min=1, max=90)
    disease = fake.word().capitalize()
    contact = f"+92-{fake.random_number(digits=10, fix_len=True)}"

    status = random.choice(["admitted", "discharged"])

    # Insert patient
    cur.execute(
        "INSERT INTO patients (name, age, disease, contact, Status) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (name, age, disease, contact, status)
    )
    patient_id = cur.fetchone()[0]

    # Unique timestamp using microseconds
    current_time = datetime.now().strftime('%y%m%d%H%M%S%f')  # %f for microseconds

    visit_date_str = f"P{current_time}{patient_id}"

    cur.execute("UPDATE patients SET visit_date=%s WHERE id=%s", (visit_date_str, patient_id))

conn.commit()
conn.close()

print("✔ 1000 dummy patients inserted successfully with unique visit_date!")
