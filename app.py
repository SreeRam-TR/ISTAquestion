from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
import google.generativeai as genai
from dotenv import load_dotenv
import os

import json, re

load_dotenv()

# Supabase Init
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Gemini Init
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("submit.html")

@app.route("/view")
def view_page():
    # Fetch all unique tags
    response = supabase.table("questions").select("tag").execute()
    
    tags = sorted(list({row["tag"] for row in response.data}))
    return render_template("view.html", tags=tags)

@app.route("/ask", methods=["POST"])
def ask():
    question = request.form["question"]
    company = request.form.get("company", None)

    prompt = f"""
    You are an optimistic AI for interview students.
    1️⃣ Fix grammar of the question
    2️⃣ Identify the single BEST technology tag
       (Examples: React, Python, JavaScript, HTML, CSS, OOPS, DB, Backend, OS)

    Return JSON ONLY:
    {{
      "corrected": "...",
      "tag": "..."
    }}

    Question: "{question}"
    """

    ai = model.generate_content(prompt)
    result = ai.text

    cleaned = re.sub(r"```json|```", "", result).strip()

    result = json.loads(cleaned)
    corrected = result["corrected"]
    tag = result["tag"]

    supabase.table("questions").insert({
        "original_question": question,
        "corrected_question": corrected,
        "tag": tag,
        "company_name": company if company else None
    }).execute()

    return jsonify({"status": "success", "corrected": corrected, "tag": tag})

@app.route("/questions/<tag>")
def get_questions(tag):
    response = supabase.table("questions").select("*").eq("tag", tag).execute()
    return jsonify(response.data)

if __name__ == "__main__":
    app.run(debug=True)
