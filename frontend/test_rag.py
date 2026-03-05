
import requests
import json

url = 'http://localhost:8000/api/debug/rag-test/'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcwNzA1MjcxLCJpYXQiOjE3NzA3MDQ5NzEsImp0aSI6ImI5MjZhMjgyNmU1ZjRmMjk4OGE3OWE2YWM2MjlhMDAyIiwidXNlcl9pZCI6IjEifQ.MCUI68pn4Wi2b2AymLlsSioepWIjGE31o3jH1Lx25t8',
    'Content-Type': 'application/json'
}
data = {'bot_id': 17, 'question': 'What platform is the best?'}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f'Status Code: {response.status_code}')
    print(response.text)
except Exception as e:
    print(e)

