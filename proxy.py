import requests
import json
import time

PROXY_URI = 'http://140.136.150.68:5010/'

current_proxy = None

def get_proxy():
    pass_flag = True
    while True:
        try:
            res = requests.get(f"{PROXY_URI}/get/")
        except json.decoder.JSONDecodeError:
            pass_flag = False
            print('Too many requests, sleeping...')
            time.sleep(5.0)
        if pass_flag:
            break
    print(res.text)
    return res.json()

def delete_proxy(proxy):
    requests.get(f"{PROXY_URI}/delete/?proxy={proxy}")

def store_proxy(proxy):
    with open('proxy.txt', 'w') as f:
        f.write(f)

def get_stored_proxy():
    try:
        with open('proxy.txt', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return get_proxy().get("proxy")

def getHtml():
    global current_proxy
    retry_count = 5
    current_proxy = get_stored_proxy()
    while True:
        print(f'Tryin proxy: {current_proxy}')
        while retry_count > 0:
            try:
                html = requests.get('http://www.example.com',
                    proxies={"http": "http://{}".format(current_proxy)},
                    timeout=5)
                store_proxy(current_proxy)
                return html
            except Exception:
                retry_count -= 1
        delete_proxy(current_proxy)
        # Get a new proxy
        current_proxy = get_proxy().get("proxy")
        retry_count = 5

if __name__ == '__main__':
    print(getHtml().text)