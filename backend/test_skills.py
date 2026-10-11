import requests


# =========================
# ADD TEACH SKILL
# =========================

url = "http://127.0.0.1:5000/api/skills"

data = {
    "student_id": 1,
    "skill_name": "Python",
    "skill_type": "TEACH",
    "category": "Programming",
    "description": "I can teach Python basics"
}

response = requests.post(url, json=data)

print("ADD SKILL")
print("Status Code:", response.status_code)
print(response.json())


# =========================
# ADD LEARN SKILL
# =========================

data = {
    "student_id": 1,
    "skill_name": "Java",
    "skill_type": "LEARN",
    "category": "Programming",
    "description": "I want to learn Java"
}

response = requests.post(url, json=data)

print("\nADD LEARN SKILL")
print("Status Code:", response.status_code)
print(response.json())


# =========================
# GET ALL SKILLS
# =========================

get_url = "http://127.0.0.1:5000/api/skills/1"

response = requests.get(get_url)

print("\nGET SKILLS")
print("Status Code:", response.status_code)
print(response.json())