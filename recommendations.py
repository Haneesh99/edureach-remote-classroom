LEVELS = {
    "Struggling":     (0, 40,  "Review basic concepts in {course}. Extra materials flagged."),
    "Needs Practice": (40, 60, "You are making progress in {course}. Attempt more practice quizzes."),
    "On Track":       (60, 80, "Good work in {course}. Explore the advanced materials."),
    "Excellent":      (80, 101,"Outstanding performance in {course}. You are ready for the next level."),
}

def get_recommendation(score_percent, course_name):
    for level, (min_score, max_score, message_template) in LEVELS.items():
        if min_score <= score_percent < max_score:
            message = message_template.format(course=course_name)
            flag_teacher = score_percent < 60
            return {
                "level": level,
                "message": message,
                "flag_teacher": flag_teacher
            }
    return {
        "level": "Unknown",
        "message": "Unable to determine recommendation.",
        "flag_teacher": False
    }
