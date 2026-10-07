import json
import os

def load_questions():
    json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'questions.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading questions.json: {e}")
        return []

def get_questions_for_role(role_name, limit=5, **kwargs):
    data = load_questions()
    questions = []

    # Case 1: Root JSON is a list [...]
    if isinstance(data, list):
        for item in data:
            # Check if list contains role objects like {"role": "Software Developer", "questions": [...]}
            role_title = item.get('role', '') or item.get('name', '') or item.get('role_name', '')
            if role_title.lower() == role_name.lower():
                questions = item.get('questions', [])
                break

    # Case 2: Root JSON is a dictionary {...}
    elif isinstance(data, dict):
        roles_data = data.get('roles', data)
        
        if isinstance(roles_data, list):
            for role_obj in roles_data:
                role_title = role_obj.get('name', '') or role_obj.get('role', '')
                if role_title.lower() == role_name.lower():
                    questions = role_obj.get('questions', [])
                    break
        elif isinstance(roles_data, dict):
            questions = roles_data.get(role_name, [])
            if not questions:
                for r_key, q_list in roles_data.items():
                    if r_key.lower() == role_name.lower():
                        questions = q_list
                        break

    return questions[:limit]

def get_question_by_id(role_name, q_id):
    questions = get_questions_for_role(role_name, limit=25)
    for q in questions:
        if q.get('id') == q_id:
            return q
    return None