import requests


# =========================
# SEARCH PYTHON TEACHERS
# =========================

url = "http://127.0.0.1:5000/api/search-teachers"

params = {
    "skill": "Python"
}


response = requests.get(
    url,
    params=params
)


print("SEARCH TEACHERS")

print("Status Code:", response.status_code)

print(response.json())