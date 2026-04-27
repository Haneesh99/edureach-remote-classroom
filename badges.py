BADGES = {
    "First Login":           {"color": "#C4622D", "condition": "has_logged_in"},
    "Assignment Submitted":  {"color": "#2D5016", "condition": "has_submitted"},
    "Quiz Master":           {"color": "#8B6914", "condition": "quiz_score_100"},
    "Perfect Attendance":    {"color": "#1A4A6B", "condition": "full_attendance"},
    "Top Performer":         {"color": "#6B2D8B", "condition": "avg_score_above_80"},
}

def compute_badges(student_id, db):
    earned = []
    
    if db.has_logged_in(student_id):
        earned.append("First Login")
    
    if db.has_submitted_assignment(student_id):
        earned.append("Assignment Submitted")
    
    if db.has_perfect_quiz(student_id):
        earned.append("Quiz Master")
    
    if db.has_full_attendance(student_id):
        earned.append("Perfect Attendance")
    
    avg_score = db.get_average_score(student_id)
    if avg_score and avg_score >= 80:
        earned.append("Top Performer")
    
    return earned

def get_badge_details(badge_name):
    return BADGES.get(badge_name, {"color": "#888888", "condition": "unknown"})
