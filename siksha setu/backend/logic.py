import PyPDF2
import random
import re
from collections import Counter

student_score = 0


# ---------------- PDF LOADER ----------------

def load_pdf(path):
    text = ""
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "
    return text.lower()


# ---------------- CLEAN WORDS ----------------

def clean_words(text):
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text)

    stopwords = {
        "this","that","with","from","have","will","were","their",
        "there","about","which","when","what","where","your",
        "been","into","more","than","also","such","these",
        "because","while","each","other","using","used",
        "some","very","just","then","they","them","would",
        "could","should","shall","does","done","make","made",
        "take","took","give","given","come","came","well",
        "over","under","after","before","through","during"
    }

    return [w for w in words if w not in stopwords]


# ============================================================
# 🔥 AI TUTOR (COGNITIVE + CONTEXT BASED)
# ============================================================

def handle_message(msg, notes, profile):

    if not notes:
        return "📂 Please upload PDF notes first."

    cognitive = profile.get("cognitive_score", 50)
    message = msg.lower()

    # -------- INTENT --------

    if "quiz" in message or "mcq" in message or "question" in message:
        return generate_mcq(notes)

    if "summarize" in message or "summary" in message:
        summary = extract_summary(notes)
        return "📄 **Summary:**\n\n" + summary

    if "topics" in message or "chapter" in message or "key" in message:
        words = clean_words(notes)
        freq = Counter(words)
        top = freq.most_common(8)
        topics_str = "\n".join([f"• **{t[0].title()}**" for t in top])
        return f"🗝️ **Key Topics from your notes:**\n\n{topics_str}"

    if "simplify" in message or "simple" in message or "explain" in message:
        best_match = find_relevant_paragraph(message, notes)
        return f"💡 **Simple Explanation:**\n\n{best_match[:500]}...\n\n🎯 Tip: Re-read this in your own words to lock it in."

    # -------- KEYWORD EXTRACTION --------

    best_match = find_relevant_paragraph(message, notes)

    if not best_match:
        best_match = notes[:600]

    # -------- COGNITIVE ADAPTATION --------

    if cognitive < 40:
        return f"""
📘 **Simple Explanation:**

{best_match[:400]}...

📌 **Key Idea:**
Focus on understanding the basic meaning first.

🎯 **Tip:** Revise this again within 24 hours for better retention.
"""

    elif cognitive < 70:
        return f"""
📘 **Concept Explanation:**

{best_match[:600]}...

📌 **Important Points:**
- Understand the core definitions
- Practice with examples
- Write short answers to reinforce learning

📝 **Practice Question:**
Explain this concept in 3–4 lines in your own words.
"""

    else:
        return f"""
📘 **Advanced Explanation:**

{best_match[:800]}...

🎯 **Exam Insight:**
Expect both conceptual and application-based questions on this topic.

⚠️ **Common Trap:**
Students often confuse related subtopics — revise carefully and note edge cases.

📝 **Challenge Question:**
How would you apply this concept in a real-world situation?
"""


# ============================================================
# HELPER: FIND RELEVANT PARAGRAPH
# ============================================================

def find_relevant_paragraph(message, notes):
    keywords = re.findall(r'\b[a-zA-Z]{4,}\b', message)
    paragraphs = re.split(r'[.\n]', notes)
    best_match = ""
    best_score = 0

    for para in paragraphs:
        score = sum(1 for w in keywords if w in para)
        if score > best_score:
            best_score = score
            best_match = para

    return best_match


# ============================================================
# HELPER: EXTRACT SUMMARY
# ============================================================

def extract_summary(notes):
    sentences = re.split(r'[.!?]', notes)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
    if not sentences:
        return notes[:800] + "..."
    summary = " ".join(sentences[:6])
    return summary[:800] + "..."


# ============================================================
# MCQ GENERATOR
# ============================================================

def generate_mcq(notes):
    words = clean_words(notes)

    if len(words) < 20:
        return "📝 **Sample Quiz:**\n\n1) What is AI?\n\nA) Robot  B) Intelligence  C) Car  D) Phone\n\n✅ Answer: B"

    answer = random.choice(words)
    options = random.sample([w for w in words if w != answer], min(3, len(words)-1))
    options.append(answer)
    random.shuffle(options)

    labels = ["A", "B", "C", "D"]
    answer_label = labels[options.index(answer)]

    options_str = "\n".join([f"{labels[i]}) {opt.title()}" for i, opt in enumerate(options)])

    return f"""
📝 **MCQ Quiz:**

Which term appeared in your study notes?

{options_str}

✅ **Correct Answer:** {answer_label}) {answer.title()}
"""


# ============================================================
# MOCK QUESTION GENERATOR
# ============================================================

def generate_mock_questions(notes):

    if not notes:
        return []

    words = list(set(clean_words(notes)))

    if len(words) < 20:
        return [{
            "question": "What is Artificial Intelligence?",
            "options": ["Machine Learning", "Robotics", "Deep AI", "Biology"],
            "answer": "Deep AI"
        }]

    questions = []

    for i in range(10):
        correct = random.choice(words)
        distractors = random.sample([w for w in words if w != correct], min(3, len(words)-1))
        options = distractors + [correct]
        random.shuffle(options)

        questions.append({
            "question": f"Which term appeared in your syllabus?",
            "options": [o.title() for o in options],
            "answer": correct.title()
        })

    return questions


# ============================================================
# FUN QUIZ QUESTION GENERATOR
# ============================================================

FUN_QUESTIONS_BANK = [
    {
        "question": "What does 'AI' stand for?",
        "options": ["Artificial Intelligence", "Auto Interaction", "Automated Input", "Advanced Internet"],
        "answer": "Artificial Intelligence"
    },
    {
        "question": "Which planet is known as the Red Planet?",
        "options": ["Earth", "Mars", "Jupiter", "Saturn"],
        "answer": "Mars"
    },
    {
        "question": "What is the powerhouse of the cell?",
        "options": ["Nucleus", "Mitochondria", "Ribosome", "Golgi Body"],
        "answer": "Mitochondria"
    },
    {
        "question": "How many bones are in the adult human body?",
        "options": ["206", "186", "226", "196"],
        "answer": "206"
    },
    {
        "question": "What is Newton's First Law of Motion?",
        "options": ["Energy conservation", "Law of Inertia", "Action-Reaction", "Law of Gravity"],
        "answer": "Law of Inertia"
    },
    {
        "question": "What is the chemical symbol for Gold?",
        "options": ["Gd", "Go", "Au", "Ag"],
        "answer": "Au"
    },
    {
        "question": "Which country invented paper?",
        "options": ["Egypt", "India", "China", "Greece"],
        "answer": "China"
    },
    {
        "question": "What does DNA stand for?",
        "options": ["Deoxyribonucleic Acid", "Digital Neural Algorithm", "Dynamic Nerve Acid", "Dense Nucleic Agent"],
        "answer": "Deoxyribonucleic Acid"
    },
    {
        "question": "Who formulated the theory of relativity?",
        "options": ["Newton", "Einstein", "Hawking", "Darwin"],
        "answer": "Einstein"
    },
    {
        "question": "What is the speed of light in vacuum?",
        "options": ["3×10⁸ m/s", "3×10⁶ m/s", "3×10⁵ m/s", "3×10⁷ m/s"],
        "answer": "3×10⁸ m/s"
    }
]

def generate_fun_quiz_question(notes=None):
    """Generate a fun quiz question, optionally from PDF notes."""

    if notes:
        words = clean_words(notes)
        if len(words) >= 20:
            # Try to create a question from notes
            correct = random.choice(words)
            distractors = random.sample([w for w in words if w != correct], min(3, len(words)-1))
            options = distractors + [correct]
            random.shuffle(options)
            return {
                "question": "Which term appeared in your uploaded study material?",
                "options": [o.title() for o in options],
                "answer": correct.title()
            }

    # Fallback to static bank
    return random.choice(FUN_QUESTIONS_BANK)


# ============================================================
# EXAM PREPARATION (COGNITIVE-BASED)
# ============================================================

def generate_study_plan(notes, profile):

    if not notes:
        return {"error": "No syllabus uploaded."}

    words = clean_words(notes)
    freq = Counter(words)
    top_topics = freq.most_common(15)

    cognitive = profile.get("cognitive_score", 50)
    weak_topics = profile.get("weak_topics", {})
    avg_accuracy = profile.get("average_accuracy", 50)

    predicted_score = round(
        (0.5 * avg_accuracy) +
        (0.3 * cognitive) +
        (0.2 * (100 - len(weak_topics) * 5)),
        2
    )

    if cognitive < 40:
        mode = "Foundation Mode"
        strategy = "Focus on basics and daily revision. Spend more time understanding definitions."
        mock_plan = "Mock test every 3 days"
        topics_per_day = 2

    elif cognitive < 70:
        mode = "Balanced Mode"
        strategy = "Balance concept understanding with MCQ practice. Focus on weak areas."
        mock_plan = "Mock test every 2 days"
        topics_per_day = 3

    else:
        mode = "Advanced Mode"
        strategy = "Time-bound mocks with PYQs. Focus on speed and accuracy."
        mock_plan = "Daily timed mock test"
        topics_per_day = 4

    weak_priority = sorted(weak_topics.items(), key=lambda x: x[1])

    # Build a 7-day study plan
    all_topics = [t[0].title() for t in top_topics]
    plan_days = []

    days = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]
    topic_idx = 0

    for day in days:
        day_topics = []
        for _ in range(topics_per_day):
            if topic_idx < len(all_topics):
                day_topics.append(all_topics[topic_idx])
                topic_idx += 1
        plan_days.append({
            "day": day,
            "topics": day_topics,
            "focus": "Core concept revision"
        })

    return {
        "study_mode": mode,
        "strategy": strategy,
        "mock_plan": mock_plan,
        "predicted_exam_score": min(100, predicted_score),
        "priority_topics": [t[0] for t in weak_priority[:5]],
        "top_syllabus_topics": [t[0].title() for t in top_topics[:8]],
        "plan": plan_days
    }


# ============================================================
# SMART REVISION
# ============================================================

def generate_revision_plan(notes, profile):

    if not notes:
        return {"error": "No syllabus uploaded."}

    words = clean_words(notes)
    freq = Counter(words)
    top_topics = freq.most_common(8)

    cognitive = profile.get("cognitive_score", 50)
    weak_topics = profile.get("weak_topics", {})

    revision_list = []

    for topic, count in top_topics:
        if topic in weak_topics:
            revision_list.append({
                "topic": topic.title(),
                "priority": "High",
                "weight": min(90, 40 + count)
            })
        else:
            revision_list.append({
                "topic": topic.title(),
                "priority": "Medium",
                "weight": min(75, 30 + count)
            })

    if cognitive < 40:
        frequency = "Revise every 24 hours"
        tip = "Short sessions of 20–30 minutes work best for you."
    elif cognitive < 70:
        frequency = "Revise every 48 hours"
        tip = "Mix reading with practice questions for better retention."
    else:
        frequency = "Revise every 72 hours"
        tip = "Focus on application-based practice and timed revision."

    priority_topics = revision_list[:3]

    return {
        "revision_frequency": frequency,
        "tip": tip,
        "revision_plan": revision_list,
        "priority_topics": [r["topic"] for r in revision_list[:6] if r],
        "cognitive_score": cognitive
    }


# ============================================================
# LEADERBOARD DATA
# ============================================================

def get_leaderboard_data(mode="individual"):
    individual_data = [
        {"name": "Rahul Sharma", "score": 985, "improvement": "Integral Calculus", "color": "#6C5CE7", "streak": 12},
        {"name": "Priya Singh", "score": 920, "improvement": "Organic Chemistry", "color": "#E2725B", "streak": 9},
        {"name": "Amit Patel", "score": 855, "improvement": "Quantum Mechanics", "color": "#27AE60", "streak": 7},
        {"name": "Sanya Iyer", "score": 790, "improvement": "Statistical Physics", "color": "#DAA520", "streak": 5},
        {"name": "Kevin Joy", "score": 710, "improvement": "Linear Algebra", "color": "#4A90E2", "streak": 4},
        {"name": "Meera Nair", "score": 660, "improvement": "Thermodynamics", "color": "#E74C3C", "streak": 3},
        {"name": "Arjun Gupta", "score": 620, "improvement": "Electrostatics", "color": "#1ABC9C", "streak": 2},
    ]

    group_data = [
        {"name": "Team Alpha", "score": 2800, "improvement": "Collaborative Logic", "color": "#FF7675", "streak": 8},
        {"name": "Study Warriors", "score": 2650, "improvement": "Problem Solving Speed", "color": "#74B9FF", "streak": 6},
        {"name": "AI Explorers", "score": 2400, "improvement": "Pattern Recognition", "color": "#55E6C1", "streak": 5},
        {"name": "Science Stars", "score": 2100, "improvement": "Chemistry Mastery", "color": "#FDCB6E", "streak": 3},
        {"name": "Math Masters", "score": 1950, "improvement": "Calculus & Algebra", "color": "#A29BFE", "streak": 2},
    ]

    if mode == "group":
        return {"leaderboard": group_data, "mode": "group"}

    return {"leaderboard": individual_data, "mode": "individual"}
