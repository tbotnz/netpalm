
import requests

hosts = ["10.0.2.17","10.0.2.18","10.0.2.19","10.0.2.20","10.0.2.21","10.0.2.22","10.0.2.23","10.0.2.24","10.0.2.25","10.0.2.26","10.0.2.27","10.0.2.28","10.0.2.29","10.0.2.30","10.0.2.31", "10.0.2.32", "10.0.2.33"]
try:
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'x-api-key': 'xxxxxxx'}
    for host in hosts:
        data = {
        "host":host,
        "library": "netmiko",
        "driver":"cisco_ios",
        "config": "hostname cat\nend",
        "username": "admin",
        "password": "admin"
        }       
        r = requests.post('http://127.0.0.1:9000/pushconfig', json=data, headers=headers)
        print (r.content)
except Exception as e:
    print(str(e))



