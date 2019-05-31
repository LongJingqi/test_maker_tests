import time
import json
import threading
import os

import requests


HEADERS = {
    "Content-Type": "application/json"
}
BASE_URL = "http://gc21131138.imwork.net:20430/test-maker/web/admin/"
LOGIN_URL = BASE_URL + "login.action"
WELCOME_URL = BASE_URL + "welcome.action"


class LoadTestThread(threading.Thread):
    # latency 为每次请求 welcome page 时间间隔
    def __init__(self, username, password, thread_id, run_time=1, latency=0.1):
        super(LoadTestThread, self).__init__()
        self.thread_id = thread_id
        self.username = username
        self.password = password
        self.run_time = run_time
        self.latency = latency

    def run(self):
        login_time = login(self.username, self.password)
        results = []
        for i in range(self.run_time):
            wel_time = get_welcome()
            results.append({"run_time": i+1, "welcome_latency": wel_time})
            time.sleep(self.latency)

        f = open(os.path.join("result", str(self.thread_id)+".json"), "w+")
        f.write(json.dumps({"thread_id": self.thread_id, "login_time": login_time, "results": results}, indent=4))
        f.close()


class LoadTestThreadGroup:
    # latency 为相邻线程之间启动时间间隔
    def __init__(self, users, latency=0.1, run_time=1, request_latency=0.1):
        self.users = users
        self.latency = latency
        self.run_time = run_time
        self.request_lat = request_latency

    def run(self):
        threads = []
        for i in range(len(self.users)):
            print("starting thread " + str(i+1) + "...")
            username = self.users[i].get("username")
            password = self.users[i].get("password")
            thread = LoadTestThread(username, password, i+1, self.run_time, self.request_lat)
            threads.append(thread)
            thread.start()
            time.sleep(self.latency)

        for thread in threads:
            thread.join()
            print("thread %s done." % thread.thread_id)
        print("test done!")


def login(username, password):
    login_data = {
        "username": username,
        "password": password
    }
    start = int(time.time() * 1000)
    response = requests.post(url=LOGIN_URL, json=login_data)
    if response.status_code != 200:
        return -1
    end = int(time.time() * 1000)
    return end-start


def get_welcome():
    start = int(time.time() * 1000)
    response = requests.get(url=WELCOME_URL)
    if response.status_code != 200:
        return -1
    end = int(time.time() * 1000)
    return end-start


def read_users():
    try:
        f = open("users.json")
        data = f.read()
        return json.loads(data)
    except FileNotFoundError:
        return []


if __name__ == "__main__":
    users_input = read_users()
    group = LoadTestThreadGroup(users_input)
    group.run()