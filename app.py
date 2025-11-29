from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
import psycopg
import json, re, os

load_dotenv()


DB_URL = os.getenv("DATABASE_URL")

conn = psycopg.connect(DB_URL)
cursor = conn.cursor()

# Gemini Init
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("submit.html")


@app.route("/view")
def view_page():
    cursor.execute("SELECT DISTINCT tag FROM questions;")
    rows = cursor.fetchall()
    tags = sorted([row[0] for row in rows])
    return render_template("view.html", tags=tags)


@app.route("/ask", methods=["POST"])
def ask():
    question = request.form["question"]
    company = request.form.get("company", None)

    prompt = f"""
    You are an optimistic AI for interview students.
    1️⃣ Fix grammar of the question
    2️⃣ Identify the single BEST technology tag or HR question tag also
       (Examples: React, Python, JavaScript, HTML, CSS, OOPS, DB, Backend, OS)

    Return JSON ONLY:
    {{
      "corrected": "...",
      "tag": "..."
    }}

    Question: "{question}"
    """

    ai = model.generate_content(prompt)
    cleaned = re.sub(r"```json|```", "", ai.text).strip()
    result = json.loads(cleaned)

    corrected = result["corrected"]
    tag = result["tag"]

    cursor.execute(
        "INSERT INTO questions (original_question, corrected_question, tag, company_name) VALUES (%s, %s, %s, %s)",
        (question, corrected, tag, company)
    )
    conn.commit()

    return jsonify({"status": "success", "corrected": corrected, "tag": tag})


@app.route("/questions/<tag>")
def get_questions(tag):
    cursor.execute("SELECT * FROM questions WHERE tag = %s;", (tag,))
    rows = cursor.fetchall()

    data = []
    for row in rows:
        data.append({
            "id": row[0],
            "original_question": row[1],
            "corrected_question": row[2],
            "tag": row[3],
            "company_name": row[4]
        })

    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
