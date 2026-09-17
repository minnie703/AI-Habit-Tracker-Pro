from flask import Flask, render_template, request, redirect, send_file
import sqlite3
import matplotlib.pyplot as plt
import io
import google.generativeai as genai
from reportlab.pdfgen import canvas

app = Flask(__name__)

# ------------------
# Gemini Setup
# ------------------

genai.configure(api_key="YOUR_API_KEY")

model = genai.GenerativeModel(
    "gemini-1.5-flash"
)

# ------------------
# Database Setup
# ------------------

def init_db():

    conn = sqlite3.connect("habit.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS habits(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        streak INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ------------------
# Home
# ------------------

@app.route("/")
def home():
     
    conn = sqlite3.connect("habit.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM habits
    ORDER BY id DESC
    """)

    habits = cur.fetchall()

    conn.close()

    total_habits = len(habits)

    highest_streak = 0
    total_streaks = 0
    best_habit = "No Habits"

    if habits:

        highest_streak = max(
            habit[2]
            for habit in habits
        )

        total_streaks = sum(
            habit[2]
            for habit in habits
        )
        badge = "🌱 Beginner"

        if highest_streak >= 5:
            badge = "🔥 Consistent"

        if highest_streak >= 15:
           badge = "🏆 Habit Master"
     
        if highest_streak >= 30:
           badge = "👑 Legend"

        best_habit = max(
            habits,
            key=lambda x: x[2]
        )[1]

    ai_advice = ""

    if habits:

        prompt = f"""
User Habit Statistics

Total Habits: {total_habits}

Highest Streak: {highest_streak}

Best Habit: {best_habit}

Total Streaks: {total_streaks}

Give:

1 short motivation quote

1 productivity tip

Keep response under 60 words.
"""

        try:

            response = model.generate_content(
                prompt
            )

            ai_advice = response.text

        except:

            ai_advice = (
                "Stay consistent. Small daily actions create big results."
            )

    else:

        ai_advice = (
            "Add your first habit and start building momentum."
        )

    return render_template(
    "index.html",
    habits=habits,
    total_habits=total_habits,
    highest_streak=highest_streak,
    total_streaks=total_streaks,
    best_habit=best_habit,
    ai_advice=ai_advice,
    badge=badge
)

# ------------------
# Add Habit
# ------------------

@app.route("/add", methods=["POST"])
def add():

    habit = request.form["habit"]

    conn = sqlite3.connect("habit.db")
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO habits(name)
    VALUES(?)
    """, (habit,))

    conn.commit()
    conn.close()

    return redirect("/")

# ------------------
# Complete Habit
# ------------------

@app.route("/complete/<int:id>")
def complete(id):

    conn = sqlite3.connect("habit.db")
    cur = conn.cursor()

    cur.execute("""
    UPDATE habits
    SET streak = streak + 1
    WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/")

# ------------------
# Delete Habit
# ------------------

@app.route("/delete/<int:id>")
def delete(id):

    conn = sqlite3.connect("habit.db")
    cur = conn.cursor()

    cur.execute("""
    DELETE FROM habits
    WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/")

# ------------------
# Chart
# ------------------

@app.route("/chart")
def chart():

    conn = sqlite3.connect("habit.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT name, streak
    FROM habits
    """)

    data = cur.fetchall()

    conn.close()

    labels = [x[0] for x in data]
    values = [x[1] for x in data]

    plt.figure(figsize=(6, 4))

    plt.bar(labels, values)

    plt.title("Habit Streak Analytics")

    img = io.BytesIO()

    plt.savefig(
        img,
        format="png",
        bbox_inches="tight"
    )

    plt.close()

    img.seek(0)

    return send_file(
        img,
        mimetype="image/png"
    )

# ------------------
# Run App
# ------------------

@app.route("/report")
def report():

    conn = sqlite3.connect("habit.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT name, streak
    FROM habits
    """)

    habits = cur.fetchall()

    conn.close()

    pdf_file = "habit_report.pdf"

    c = canvas.Canvas(pdf_file)

    c.setFont(
        "Helvetica-Bold",
        18
    )

    c.drawString(
        50,
        800,
        "AI Habit Tracker Pro Report"
    )

    y = 760

    for habit in habits:

        c.drawString(
            50,
            y,
            f"{habit[0]} - Streak: {habit[1]}"
        )

        y -= 25

    c.save()

    return send_file(
        pdf_file,
        as_attachment=True
    )

if __name__ == "__main__":
    app.run(debug=True)