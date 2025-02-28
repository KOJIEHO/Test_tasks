import requests


IP = ''
if IP == '': IP = '127.0.0.1'
url = f'http://{IP}:8000/cash_machine/'

data = {
    "items": [1, 2, 3]
}
response = requests.post(url, json=data)

if response.status_code == 200:
    with open(f'Grossbit/cash_machine/media/qr_code.png', 'wb') as f:
        f.write(response.content)
else:
    print(f"Ошибка: {response.status_code}")
    