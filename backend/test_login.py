import requests


url = "http://127.0.0.1:5000/api/login"


data = {
    "email": "test@skillswap.com",
    "password": "Test@123"
}


response = requests.post(
    url,
    json=data
)


print(response.status_code)

print(response.json())