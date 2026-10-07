import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def calculate_keyword_score(user_answer, keywords):
    if not keywords:
        return 100.0
    
    user_text_lower = user_answer.lower()
    matched_count = 0
    
    for kw in keywords:
        pattern = r'\b' + re.escape(kw.lower()) + r'\b'
        if re.search(pattern, user_text_lower):
            matched_count += 1
            
    return round((matched_count / len(keywords)) * 100, 1)

def calculate_semantic_score(user_answer, reference_answer):
    if not user_answer.strip() or not reference_answer.strip():
        return 0.0
        
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([user_answer, reference_answer])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return round(float(similarity) * 100, 1)
    except Exception as e:
        print(f"Error computing cosine similarity: {e}")
        return 50.0

def calculate_completeness_score(user_answer):
    words = len(user_answer.strip().split())
    if words == 0:
        return 0.0
    elif words < 10:
        return 30.0
    elif words < 25:
        return 65.0
    elif words < 50:
        return 85.0
    else:
        return 100.0

def evaluate_answer(candidate_answer="", user_answer="", reference_answer="", keywords=None, difficulty="Medium", **kwargs):
    # Support both candidate_answer and user_answer keyword names
    actual_answer = user_answer if user_answer else candidate_answer
    if keywords is None:
        keywords = []

    keyword_score = calculate_keyword_score(actual_answer, keywords)
    semantic_score = calculate_semantic_score(actual_answer, reference_answer)
    completeness_score = calculate_completeness_score(actual_answer)

    # Weighted composite score
    final_score = round(
        (semantic_score * 0.45) + 
        (keyword_score * 0.35) + 
        (completeness_score * 0.20), 1
    )

    feedback = generate_feedback(final_score, keyword_score, semantic_score, completeness_score)

    return {
        "semantic_score": semantic_score,
        "keyword_score": keyword_score,
        "completeness_score": completeness_score,
        "final_score": final_score,
        "feedback": feedback
    }

def generate_feedback(final_score, keyword_score, semantic_score, completeness_score):
    if final_score >= 80:
        return "Excellent response! Well-structured with accurate key concepts."
    elif final_score >= 60:
        return "Good effort. Core concepts are present, but additional technical depth is recommended."
    elif final_score >= 40:
        return "Partial response. Key industry terms and deeper explanations were missing."
    else:
        return "Needs improvement. The response lacked essential technical terminology and conceptual clarity."

def generate_recommendation(overall_score):
    if overall_score >= 80:
        return {"status": "STRONG HIRE", "class": "badge-success"}
    elif overall_score >= 65:
        return {"status": "HIRE", "class": "badge-primary"}
    elif overall_score >= 50:
        return {"status": "CONSIDER", "class": "badge-warning"}
    else:
        return {"status": "NOT RECOMMENDED", "class": "badge-danger"}