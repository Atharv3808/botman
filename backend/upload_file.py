
import requests

url = 'http://localhost:8000/api/bot/17/knowledge/'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcwNzA2MzI0LCJpYXQiOjE3NzA3MDYwMjQsImp0aSI6IjhkYzE5Njk3NTRjMTQxZGQ5NTI5NGYyYjcyMjhkOTE0IiwidXNlcl9pZCI6IjEifQ.E496udv0ve5LDpbnaQxLtOcKPZ966UZX9JEGtdHknd4'
}
files = {'file': open('rag_test_v3.txt', 'rb')}

try:
    response = requests.post(url, headers=headers, files=files)
    print(f'Status Code: {response.status_code}')
    print(response.text)
except Exception as e:
    print(e)
