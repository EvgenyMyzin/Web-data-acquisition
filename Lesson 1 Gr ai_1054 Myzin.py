import requests
import json

url = 'https://api.github.com'
user='EvgenyMyzin'

r = requests.get(f'{url}/users/{user}/repos')

with open('repos_list.json', 'w') as f:
    json.dump(r.json(), f)

for i in r.json():
    print(i['name'])


