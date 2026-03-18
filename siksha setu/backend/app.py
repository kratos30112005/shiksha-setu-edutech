from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import os
import random
import json
from database import create_user, verify_user, get_user_profile, update_user_profile


from logic import (
    handle_message,
    load_pdf,
    generate_mock_questions,
    generate_study_plan,
    generate_revision_plan,
    generate_fun_quiz_question,
    get_leaderboard_data
)

from ml.profile_engine import create_student_profile, update_profile


app = Flask(__name__)

# ---------------- CONFIG ----------------

app.secret_key = "shiksha-setu-secret-2026"
CORS(app, supports_credentials=True)

# 🔥 In-memory storage for uploaded PDFs
uploaded_notes_storage = {}

# ---------------- SIMPLE MISTAKE COUNTER & TEST DB ----------------

QUESTIONS_BANK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions_bank.json")


def _load_questions_bank():
    try:
        if not os.path.exists(QUESTIONS_BANK_PATH):
            return {}
        with open(QUESTIONS_BANK_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print("QUESTIONS BANK LOAD ERROR:", str(e))
        return {}


def _get_bank():
    # lightweight lazy load (so edits to JSON are picked up after restart)
    return _load_questions_bank()

# In-memory global store for mistakes (simple array)
global_mistakes_list = []


# ---------------- PATH SETUP ----------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

HTML_DIR = os.path.join(FRONTEND_DIR, "html")
JS_DIR = os.path.join(FRONTEND_DIR, "js")
CSS_DIR = os.path.join(FRONTEND_DIR, "css")

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------- FRONTEND ROUTES ----------------

@app.route("/")
def home():
    return send_from_directory(HTML_DIR, "index.html")

@app.route("/html/<path:path>")
def html_files(path):
    return send_from_directory(HTML_DIR, path)

@app.route("/js/<path:path>")
def js_files(path):
    return send_from_directory(JS_DIR, path)

@app.route("/css/<path:path>")
def css_files(path):
    return send_from_directory(CSS_DIR, path)

# ---------------- LOGIN / LOGOUT ----------------

@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.json
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    
    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required"}), 400
        
    default_profile = create_student_profile()
    success, msg = create_user(name, email, password, default_profile)
    
    if success:
        session.clear()
        session["user"] = email
        session["name"] = name
        session["profile"] = default_profile
        return jsonify({"status": "ok", "user": name, "email": email})
    else:
        return jsonify({"error": msg}), 400

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    success, user_data = verify_user(email, password)
    
    if success:
        session.clear()
        session["user"] = email
        session["name"] = user_data["name"]
        
        try:
            profile = json.loads(user_data["profile_data"]) if user_data["profile_data"] else create_student_profile()
        except:
            profile = create_student_profile()
            
        session["profile"] = profile
        return jsonify({"status": "ok", "user": user_data["name"], "email": email})
    else:
        return jsonify({"error": user_data}), 401

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "ok"})

@app.route("/api/user")
def get_user():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401
        
    email = session.get("user")
    name = session.get("name", "Student")

    if "profile" not in session:
        user_data = get_user_profile(email)
        if user_data and user_data.get("profile_data"):
            try:
                session["profile"] = json.loads(user_data["profile_data"])
            except:
                session["profile"] = create_student_profile()
        else:
            session["profile"] = create_student_profile()

    profile = session.get("profile", {})

    return jsonify({
        "user": name,
        "email": email,
        "profile": profile,
        "cognitive_score": profile.get("cognitive_score", 50),
        "difficulty_level": profile.get("difficulty_level", "medium"),
        "total_attempts": profile.get("total_attempts", 0),
        "average_accuracy": profile.get("average_accuracy", 0.0)
    })

# ---------------- PDF UPLOAD ----------------

@app.route("/api/upload", methods=["POST"])
def upload_pdf():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        path = os.path.join(UPLOAD_DIR, file.filename)
        file.save(path)

        notes_text = load_pdf(path)

        if not notes_text:
            return jsonify({"error": "PDF extraction failed"}), 400

        user_id = session.get("user", "default_user")
        uploaded_notes_storage[user_id] = notes_text

        return jsonify({"status": "PDF loaded successfully", "word_count": len(notes_text.split())})

    except Exception as e:
        print("UPLOAD ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

# ---------------- AI TUTOR (COGNITIVE-AWARE) ----------------

@app.route("/api/chat", methods=["POST"])
def chat():
    user_id = session.get("user", "default_user")
    notes = uploaded_notes_storage.get(user_id)

    if not notes:
        return jsonify({"reply": "📂 Please upload your PDF notes first using the upload button above."})

    if "profile" not in session:
        session["profile"] = create_student_profile()

    profile = session.get("profile")
    msg = request.json.get("message", "")

    if not msg.strip():
        return jsonify({"reply": "Please ask me something about your notes!"})

    reply = handle_message(msg, notes, profile)
    return jsonify({"reply": reply})

# ---------------- SOLO MOCK ----------------

@app.route("/api/solo-mock", methods=["GET"])
def solo_mock():
    user_id = session.get("user", "default_user")
    notes = uploaded_notes_storage.get(user_id)

    if not notes:
        return jsonify({"error": "Upload syllabus first."})

    questions = generate_mock_questions(notes)
    return jsonify({"questions": questions})

# ---------------- FUN QUIZ ----------------

@app.route("/api/fun-quiz", methods=["GET"])
def fun_quiz():
    user_id = session.get("user", "default_user")
    notes = uploaded_notes_storage.get(user_id)
    question = generate_fun_quiz_question(notes)
    return jsonify(question)

# ---------------- PERFORMANCE ANALYSIS ----------------

@app.route("/api/analyze-performance", methods=["POST"])
def analyze_performance():
    if "profile" not in session:
        session["profile"] = create_student_profile()

    profile = session.get("profile")
    data = request.json

    try:
        updated_profile = update_profile(profile, data)
        session["profile"] = updated_profile
        
        email = session.get("user")
        if email and email != "default_user":
            update_user_profile(email, updated_profile)
    except Exception as e:
        print("PROFILE UPDATE ERROR:", str(e))
        updated_profile = profile

    cognitive = updated_profile.get("cognitive_score", 50)
    difficulty = updated_profile.get("difficulty_level", "medium")

    return jsonify({
        "cognitive_score": cognitive,
        "difficulty_level": difficulty,
        "weak_topics": updated_profile.get("weak_topics", {}),
        "strong_topics": updated_profile.get("strong_topics", {}),
        "average_accuracy": updated_profile.get("average_accuracy", 0),
        "total_attempts": updated_profile.get("total_attempts", 0)
    })

# ---------------- STUDY PLAN (Cognitive-Based) ----------------

@app.route("/api/study-plan", methods=["GET"])
def study_plan():
    user_id = session.get("user", "default_user")
    notes = uploaded_notes_storage.get(user_id)

    if not notes:
        return jsonify({"error": "📂 Please upload syllabus first."})

    if "profile" not in session:
        session["profile"] = create_student_profile()

    profile = session.get("profile")
    plan = generate_study_plan(notes, profile)

    return jsonify(plan)

# ---------------- SMART REVISION (Cognitive-Based) ----------------

@app.route("/api/smart-revision", methods=["GET"])
def smart_revision():
    user_id = session.get("user", "default_user")
    notes = uploaded_notes_storage.get(user_id)

    if not notes:
        return jsonify({"error": "📂 Please upload syllabus first."})

    if "profile" not in session:
        session["profile"] = create_student_profile()

    profile = session.get("profile")
    revision = generate_revision_plan(notes, profile)

    return jsonify(revision)

# ---------------- LEADERBOARD ----------------

@app.route("/api/leaderboard", methods=["GET"])
def leaderboard():
    mode = request.args.get("mode", "individual")
    data = get_leaderboard_data(mode)
    return jsonify(data)

# ---------------- MISTAKE COUNTER & TEST SYSTEM APIs ----------------

@app.route("/api/get-questions", methods=["GET"])
def get_questions():
    subject = request.args.get("subject")
    topic = request.args.get("topic")

    bank = _get_bank()
    if subject in bank and topic in bank[subject]:
        # Send questions without the answer key for fairness
        questions = bank[subject][topic]
        client_questions = []
        for q in questions:
            client_questions.append({
                "id": q["id"],
                "question": q["question"],
                "options": q["options"]
            })
        return jsonify({"questions": client_questions})
    
    return jsonify({"error": "No questions found for this subject and topic"}), 404

@app.route("/api/get-pdf-questions", methods=["GET"])
def get_pdf_questions():
    user_id = session.get("user", "default_user")
    notes = uploaded_notes_storage.get(user_id)
    
    if not notes:
        return jsonify({"error": "No syllabus uploaded. Please upload a PDF first."}), 400
        
    raw_questions = generate_mock_questions(notes)
    
    # Assign an ID to each and store globally or in session
    # For simplicity, we just store it in session
    for i, q in enumerate(raw_questions):
        q["id"] = f"pdf-q{i}"
        
    session["custom_pdf_questions"] = raw_questions
    session.modified = True
    
    # Format for client without answer keys
    client_questions = []
    for q in raw_questions:
        client_questions.append({
            "id": q["id"],
            "question": q["question"],
            "options": q["options"]
        })
        
    return jsonify({"questions": client_questions})

@app.route("/api/submit-test", methods=["POST"])
def submit_test():
    data = request.json
    subject = data.get("subject")
    topic = data.get("topic")
    user_answers = data.get("answers", {})  # format: {"q1": "5", "q2": "..."}
    
    if subject == "Custom PDF":
        questions = session.get("custom_pdf_questions", [])
        if not questions:
            return jsonify({"error": "Test session expired or invalid"}), 400
    else:
        bank = _get_bank()
        if subject not in bank or topic not in bank[subject]:
            return jsonify({"error": "Invalid test data"}), 400
        questions = bank[subject][topic]
    score = 0
    total = len(questions)
    results = []
    
    for q in questions:
        q_id = q["id"]
        correct_ans = q["answer"]
        user_ans = user_answers.get(q_id, "")
        
        is_correct = (correct_ans == user_ans)
        
        if is_correct:
            score += 1
        else:
            # Add to Mistake Counter
            mistake_entry = {
                "subject": subject,
                "topic": topic,
                "question": q["question"],
                "correct_answer": correct_ans,
                "user_answer": user_ans if user_ans else "Not Attempted"
            }
            global_mistakes_list.append(mistake_entry)
            
        results.append({
            "question": q["question"],
            "correct_answer": correct_ans,
            "user_answer": user_ans,
            "is_correct": is_correct
        })
        
    return jsonify({
        "score": score,
        "total": total,
        "results": results
    })


# ---------------- SUBJECT/TOPIC LISTING (no hardcoded dropdowns) ----------------

@app.route("/api/subjects", methods=["GET"])
def list_subjects():
    bank = _get_bank()
    return jsonify({"subjects": sorted(list(bank.keys()))})


@app.route("/api/topics", methods=["GET"])
def list_topics():
    subject = request.args.get("subject")
    bank = _get_bank()
    if not subject or subject not in bank:
        return jsonify({"topics": []})
    topics = list(bank[subject].keys()) if isinstance(bank[subject], dict) else []
    return jsonify({"topics": sorted(topics)})

@app.route("/api/get-mistakes", methods=["GET"])
def get_mistakes():
    # Analyze mistakes
    topic_counts = {}
    
    for m in global_mistakes_list:
        key = f"{m['subject']} - {m['topic']}"
        if key not in topic_counts:
            topic_counts[key] = {
                "subject": m["subject"],
                "topic": m["topic"],
                "count": 0,
                "mistakes": []
            }
        topic_counts[key]["count"] += 1
        topic_counts[key]["mistakes"].append(m)
        
    # Format into a sorted list of weak topics
    weak_topics = []
    for k, v in topic_counts.items():
        weak_topics.append({
            "subject": v["subject"],
            "topic": v["topic"],
            "mistake_count": v["count"],
            "details": v["mistakes"],
            "roadmap": [
                "Step 1: Revise concept",
                "Step 2: Solve examples",
                "Step 3: Practice questions",
                "Step 4: Retest"
            ]
        })
        
    # Sort by mistake count descending
    weak_topics.sort(key=lambda x: x["mistake_count"], reverse=True)
    
    return jsonify({"weak_topics": weak_topics})

# ---------------- RUN SERVER ----------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
