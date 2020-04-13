import requests
import time

HOST = 'localhost'
PORT = '8080'
STREAM_ID = 'IQk5FI4kODw'
REFRESH_URI = f'http://{HOST}:{PORT}/refresh/{STREAM_ID}'

def main():
    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed >= 1.0:
            res = requests.get(REFRESH_URI)
            print(res.json())
            start = time.time()
        time.sleep(0.5)

if __name__ == '__main__':
    main()