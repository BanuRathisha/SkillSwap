import requests


# =========================
# GET PROFILE
# =========================

url = "http://127.0.0.1:5000/api/profile/1"


response = requests.get(url)


print("Status Code:", response.status_code)

print("Response:")

print(response.json())