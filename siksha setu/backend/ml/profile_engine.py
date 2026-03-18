# ============================================
# ShikshaSetu - Student Profile Engine
# ============================================

from datetime import datetime


# --------------------------------------------
# CREATE INITIAL STUDENT PROFILE
# --------------------------------------------
def create_student_profile():
    return {
        "cognitive_score": 50,        # 0–100 scale
        "focus_score": 1.0,           # 0–1 scale
        "difficulty_level": "medium",

        "performance_history": [],    # list of attempts
        "weak_topics": {},            # topic: accuracy
        "strong_topics": {},          # topic: accuracy

        "total_attempts": 0,
        "average_accuracy": 0.0
    }


# --------------------------------------------
# UPDATE PROFILE AFTER MOCK / TEST
# --------------------------------------------
def update_profile(profile, performance_data):
    """
    performance_data expected format:
    {
        "score": int,
        "total_questions": int,
        "avg_time": float,
        "topic": str,
        "difficulty": str
    }
    """

    score = performance_data.get("score", 0)
    total = performance_data.get("total_questions", 1)
    avg_time = performance_data.get("avg_time", 0)
    topic = performance_data.get("topic", "general")
    difficulty = performance_data.get("difficulty", "medium")

    # ----------------------------------------
    # Calculate Accuracy
    # ----------------------------------------
    accuracy = (score / total) * 100

    # ----------------------------------------
    # Store Attempt History
    # ----------------------------------------
    attempt_record = {
        "timestamp": datetime.now().isoformat(),
        "accuracy": accuracy,
        "avg_time": avg_time,
        "topic": topic,
        "difficulty": difficulty
    }

    profile["performance_history"].append(attempt_record)
    profile["total_attempts"] += 1

    # ----------------------------------------
    # Update Average Accuracy
    # ----------------------------------------
    previous_avg = profile["average_accuracy"]
    attempts = profile["total_attempts"]

    new_avg = ((previous_avg * (attempts - 1)) + accuracy) / attempts
    profile["average_accuracy"] = round(new_avg, 2)

    # ----------------------------------------
    # Update Weak / Strong Topics
    # ----------------------------------------
    if accuracy < 50:
        profile["weak_topics"][topic] = round(accuracy, 2)
        if topic in profile["strong_topics"]:
            del profile["strong_topics"][topic]

    elif accuracy > 75:
        profile["strong_topics"][topic] = round(accuracy, 2)
        if topic in profile["weak_topics"]:
            del profile["weak_topics"][topic]

    # ----------------------------------------
    # Cognitive Score Adjustment (Rule-Based)
    # ----------------------------------------
    cognitive = profile["cognitive_score"]

    if accuracy > 85:
        cognitive += 3
    elif accuracy > 70:
        cognitive += 2
    elif accuracy < 40:
        cognitive -= 3
    elif accuracy < 55:
        cognitive -= 1

    # Speed influence (simple logic)
    if avg_time < 8:
        cognitive += 1
    elif avg_time > 25:
        cognitive -= 1

    # Clamp cognitive score between 0–100
    cognitive = max(0, min(100, cognitive))
    profile["cognitive_score"] = cognitive

    # ----------------------------------------
    # Update Difficulty Level
    # ----------------------------------------
    if cognitive < 40:
        profile["difficulty_level"] = "easy"
    elif cognitive < 70:
        profile["difficulty_level"] = "medium"
    else:
        profile["difficulty_level"] = "hard"

    return profile
