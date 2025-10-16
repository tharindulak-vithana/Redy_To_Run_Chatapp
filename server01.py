# server.py
import socket
import threading
import sqlite3
import json
from datetime import datetime

HOST = "0.0.0.0"
PORT = 5000
DB_FILE = "users.db"

# username -> (conn, addr)
connections = {}
lock = threading.Lock()

# ---------- Database ----------
def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT,
            phone TEXT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            recipient TEXT,
            message TEXT,
            timestamp TEXT,
            delivered INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_user(country, phone, username, password):
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("INSERT INTO users (country, phone, username, password) VALUES (?, ?, ?, ?)",
                    (country, phone, username, password))
        conn.commit()
        conn.close()
        return True, "Registered successfully"
    except sqlite3.IntegrityError:
        return False, "Username or phone already exists"
    except Exception as e:
        return False, str(e)

def verify_user(identifier, password):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT username, password FROM users WHERE phone=? OR username=?", (identifier, identifier))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False, None
    username_db, pw = row
    if pw == password:
        return True, username_db
    return False, None

def store_message(sender, recipient, message, timestamp):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (sender, recipient, message, timestamp, delivered) VALUES (?, ?, ?, ?, 0)",
                (sender, recipient, message, timestamp))
    conn.commit()
    conn.close()

def fetch_undelivered(recipient):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, sender, message, timestamp FROM messages WHERE recipient=? AND delivered=0 ORDER BY id ASC", (recipient,))
    rows = cur.fetchall()
    conn.close()
    return rows

def mark_delivered(ids):
    if not ids:
        return
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.executemany("UPDATE messages SET delivered=1 WHERE id=?", [(i,) for i in ids])
    conn.commit()
    conn.close()

def get_registered_users():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT country, phone, username FROM users ORDER BY username COLLATE NOCASE")
    rows = cur.fetchall()
    conn.close()
    return [{"country": r[0], "phone": r[1], "username": r[2]} for r in rows]

def delete_user_db(username):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()

# ---------- JSON helpers ----------
def send_json(conn, obj):
    raw = json.dumps(obj, ensure_ascii=False) + "\n"
    conn.sendall(raw.encode("utf-8"))

def recv_jsons(conn, buffer):
    try:
        data = conn.recv(4096)
        if not data:
            return None, buffer
        buffer += data.decode("utf-8", errors="ignore")
        msgs = []
        while "\n" in buffer:
            idx = buffer.index("\n")
            raw = buffer[:idx].strip()
            buffer = buffer[idx+1:]
            if not raw:
                continue
            try:
                msgs.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
        return msgs, buffer
    except ConnectionResetError:
        return None, buffer
    except Exception:
        return None, buffer

# ---------- Broadcast online users ----------
def broadcast_online():
    users = list(connections.keys())
    payload = {"action": "update_users", "users": users}
    to_remove = []
    with lock:
        for uname, (c, _) in list(connections.items()):
            try:
                send_json(c, payload)
            except Exception:
                to_remove.append(uname)
        for u in to_remove:
            try:
                connections[u][0].close()
            except:
                pass
            connections.pop(u, None)

# ---------- Client handler ----------
def handle_client(conn, addr):
    buffer = ""
    logged_user = None
    try:
        while True:
            msgs, buffer = recv_jsons(conn, buffer)
            if msgs is None:
                break
            for req in msgs:
                action = req.get("action")
                if action == "register":
                    country = req.get("country", "")
                    phone = req.get("phone", "")
                    username = req.get("username", "")
                    password = req.get("password", "")
                    if not (phone and username and password):
                        send_json(conn, {"status":"error","message":"Missing registration fields"})
                        continue
                    ok, msg = add_user(country, phone, username, password)
                    if ok:
                        send_json(conn, {"status":"success","message":msg})
                    else:
                        send_json(conn, {"status":"error","message":msg})

                elif action == "login":
                    identifier = req.get("identifier") or req.get("phone") or req.get("username")
                    password = req.get("password", "")
                    if not (identifier and password):
                        send_json(conn, {"status":"error","message":"Missing credentials"})
                        continue
                    ok, username_db = verify_user(identifier, password)
                    if ok:
                        logged_user = username_db
                        with lock:
                            connections[username_db] = (conn, addr)
                        send_json(conn, {"status":"success","message":"Login successful","username": username_db})
                        broadcast_online()
                        # deliver undelivered messages
                        undel = fetch_undelivered(username_db)
                        if undel:
                            delivered_ids = []
                            for mid, sender, message, timestamp in undel:
                                try:
                                    send_json(conn, {"action":"receive_message","from":sender,"message":message,"timestamp":timestamp})
                                    delivered_ids.append(mid)
                                except:
                                    pass
                            mark_delivered(delivered_ids)
                    else:
                        send_json(conn, {"status":"error","message":"Invalid credentials"})

                elif action == "get_online_users":
                    with lock:
                        users = list(connections.keys())
                    send_json(conn, {"status":"success","users":users})

                elif action == "send_message":
                    # PRIVATE-only message handling
                    sender = req.get("from")
                    recipient = req.get("to")
                    message = req.get("message", "")
                    timestamp = req.get("timestamp") or datetime.utcnow().strftime("%I:%M %p")
                    if not (sender and recipient and message):
                        send_json(conn, {"status":"error","message":"Missing fields for private message"})
                        continue
                    with lock:
                        target = connections.get(recipient)
                    if target:
                        try:
                            target_conn, _ = target
                            send_json(target_conn, {"action":"receive_message","from":sender,"message":message,"timestamp":timestamp})
                            # ack to sender
                            send_json(conn, {"status":"success","message":"Delivered"})
                        except Exception:
                            # if sending fails, store for later
                            store_message(sender, recipient, message, timestamp)
                            send_json(conn, {"status":"success","message":"Stored for later delivery"})
                    else:
                        # store for offline recipient
                        store_message(sender, recipient, message, timestamp)
                        send_json(conn, {"status":"success","message":"Recipient offline — stored"})

                elif action == "view_users":
                    users = get_registered_users()
                    send_json(conn, {"status":"success","users":users})

                elif action == "delete_user":
                    username = req.get("username")
                    if username:
                        delete_user_db(username)
                        with lock:
                            if username in connections:
                                try:
                                    connections[username][0].close()
                                except:
                                    pass
                                connections.pop(username, None)
                        broadcast_online()
                        send_json(conn, {"status":"success","message":"Deleted"})
                    else:
                        send_json(conn, {"status":"error","message":"username required"})

                elif action == "logout":
                    username = req.get("username")
                    if username:
                        with lock:
                            if username in connections:
                                try:
                                    connections[username][0].close()
                                except:
                                    pass
                                connections.pop(username, None)
                        broadcast_online()
                    send_json(conn, {"status":"success","message":"Logged out"})
                    return

                else:
                    send_json(conn, {"status":"error","message":"Unknown action"})
    except Exception:
        pass
    finally:
        if logged_user:
            with lock:
                if logged_user in connections and connections[logged_user][0] is conn:
                    connections.pop(logged_user, None)
            broadcast_online()
        try:
            conn.close()
        except:
            pass

# ---------- Start server ----------
def start_server():
    init_db()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(200)
    print(f"[SERVER] Listening on {HOST}:{PORT}")
    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
