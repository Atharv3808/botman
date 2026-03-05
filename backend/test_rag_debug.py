
import requests
import json

url = 'http://localhost:8000/api/debug/rag-test/'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcwNzA2MzI0LCJpYXQiOjE3NzA3MDYwMjQsImp0aSI6IjhkYzE5Njk3NTRjMTQxZGQ5NTI5NGYyYjcyMjhkOTE0IiwidXNlcl9pZCI6IjEifQ.E496udv0ve5LDpbnaQxLtOcKPZ966UZX9JEGtdHknd4',
    'Content-Type': 'application/json'
}
data = {'bot_id': 17, 'question': 'What platform is the best?'}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f'Status Code: {response.status_code}')
    print(response.text)
except Exception as e:
    print(e)
