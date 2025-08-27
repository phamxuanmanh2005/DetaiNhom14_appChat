import os
import threading

users_file = "users.txt"
users = {}      # username -> {password, nickname, friends: set(), pending: set()}
lock = threading.Lock()

# Load users từ file
if os.path.exists(users_file):
    with open(users_file, "r", encoding="utf-8") as f:
        for line in f:
            u, p, n = line.strip().split(",")
            users[u] = {"password": p, "nickname": n, "friends": set(), "pending": set()}

def save_user(username, password, nickname):
    with open(users_file, "a", encoding="utf-8") as f:
        f.write(f"{username},{password},{nickname}\n")
