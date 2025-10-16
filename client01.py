# client.py
import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import json
from datetime import datetime

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000

COUNTRY_CODES = [
    "+94 Sri Lanka", "+91 India", "+1 United States", "+44 United Kingdom", "+61 Australia",
    "+93 Afghanistan", "+213 Algeria", "+880 Bangladesh", "+86 China", "+81 Japan"
]

def send_json(sock, obj):
    raw = json.dumps(obj, ensure_ascii=False) + "\n"
    sock.sendall(raw.encode("utf-8"))

def recv_jsons(sock, buffer):
    try:
        data = sock.recv(4096)
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
            except:
                continue
        return msgs, buffer
    except:
        return None, buffer

def recv_single(sock):
    data = ""
    while "\n" not in data:
        part = sock.recv(4096).decode("utf-8")
        if not part:
            return None
        data += part
    raw, rest = data.split("\n", 1)
    try:
        return json.loads(raw)
    except:
        return None

class ChatClientGUI:
    def __init__(self, root):
        self.root = root
        root.title("Secure Chat App")
        root.geometry("980x640")
        root.configure(bg="#071226")

        self.sock = None
        self.buffer = ""
        self.username = None
        self.running = False

        self.setup_style()
        self.show_main()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 11, "bold"))
        style.configure("TLabel", font=("Segoe UI", 11))
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"))

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def connect(self):
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((SERVER_HOST, SERVER_PORT))

    # ---------- Main ----------
    def show_main(self):
        self.clear()
        card = tk.Frame(self.root, bg="#0e1b26", bd=2, relief="ridge")
        card.place(relx=0.5, rely=0.5, anchor="center", width=520, height=380)

        ttk.Label(card, text="Secure Chat App", style="Header.TLabel", background="#0e1b26", foreground="#8ee3d8").pack(pady=18)
        ttk.Button(card, text="Login", command=self.show_login, width=30).pack(pady=10)
        ttk.Button(card, text="Register", command=self.show_register, width=30).pack(pady=6)
        ttk.Button(card, text="Exit", command=self.on_exit, width=30).pack(pady=6)

    # ---------- Register ----------
    def show_register(self):
        self.clear()
        frame = tk.Frame(self.root, bg="#06121a")
        frame.place(relx=0.5, rely=0.5, anchor="center", width=640, height=520)

        ttk.Label(frame, text="Create account", style="Header.TLabel", background="#06121a", foreground="#9be7d3").pack(pady=12)
        f = tk.Frame(frame, bg="#06121a"); f.pack(pady=6)

        tk.Label(f, text="Country Code:", bg="#06121a", fg="white").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.reg_country = tk.StringVar(value=COUNTRY_CODES[0])
        ttk.Combobox(f, values=COUNTRY_CODES, textvariable=self.reg_country, width=40).grid(row=0, column=1, pady=6)

        tk.Label(f, text="Phone number:", bg="#06121a", fg="white").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        self.reg_phone = tk.StringVar()
        ttk.Entry(f, textvariable=self.reg_phone, width=42).grid(row=1, column=1, pady=6)

        tk.Label(f, text="Username:", bg="#06121a", fg="white").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        self.reg_username = tk.StringVar()
        ttk.Entry(f, textvariable=self.reg_username, width=42).grid(row=2, column=1, pady=6)

        tk.Label(f, text="Password:", bg="#06121a", fg="white").grid(row=3, column=0, sticky="w", padx=6, pady=6)
        self.reg_password = tk.StringVar()
        ttk.Entry(f, textvariable=self.reg_password, show="*", width=42).grid(row=3, column=1, pady=6)

        btnf = tk.Frame(frame, bg="#06121a"); btnf.pack(pady=12)
        ttk.Button(btnf, text="Register", command=self.do_register).grid(row=0, column=0, padx=8)
        ttk.Button(btnf, text="Back", command=self.show_main).grid(row=0, column=1, padx=8)

    def do_register(self):
        country = self.reg_country.get()
        phone = self.reg_phone.get().strip()
        username = self.reg_username.get().strip()
        password = self.reg_password.get().strip()
        if not (phone and username and password):
            messagebox.showwarning("Missing", "Please fill all fields")
            return
        try:
            self.connect()
            send_json(self.sock, {"action":"register","country":country,"phone":phone,"username":username,"password":password})
            resp = recv_single(self.sock)
            if resp and resp.get("status")=="success":
                messagebox.showinfo("Success", resp.get("message","Registered"))
                try:
                    self.sock.close()
                except:
                    pass
                self.show_login()
            else:
                messagebox.showerror("Error", resp.get("message","Registration failed"))
                try:
                    self.sock.close()
                except:
                    pass
        except Exception as e:
            messagebox.showerror("Network", str(e))

    # ---------- Login ----------
    def show_login(self):
        self.clear()
        frame = tk.Frame(self.root, bg="#06121a")
        frame.place(relx=0.5, rely=0.5, anchor="center", width=520, height=360)

        ttk.Label(frame, text="Login", style="Header.TLabel", background="#06121a", foreground="#9be7d3").pack(pady=12)
        f = tk.Frame(frame, bg="#06121a"); f.pack(pady=6)

        tk.Label(f, text="Username or Phone:", bg="#06121a", fg="white").grid(row=0,column=0, sticky="w", padx=6, pady=6)
        self.login_identifier = tk.StringVar()
        ttk.Entry(f, textvariable=self.login_identifier, width=36).grid(row=0, column=1, pady=6)

        tk.Label(f, text="Password:", bg="#06121a", fg="white").grid(row=1,column=0, sticky="w", padx=6, pady=6)
        self.login_password = tk.StringVar()
        ttk.Entry(f, textvariable=self.login_password, show="*", width=36).grid(row=1, column=1, pady=6)

        btnf = tk.Frame(frame, bg="#06121a"); btnf.pack(pady=10)
        ttk.Button(btnf, text="Login", command=self.do_login).grid(row=0, column=0, padx=8)
        ttk.Button(btnf, text="Back", command=self.show_main).grid(row=0, column=1, padx=8)

    def do_login(self):
        identifier = self.login_identifier.get().strip()
        password = self.login_password.get().strip()
        if not (identifier and password):
            messagebox.showwarning("Missing", "Enter credentials")
            return
        try:
            self.connect()
            send_json(self.sock, {"action":"login","identifier":identifier,"password":password})
            resp = recv_single(self.sock)
            if resp and resp.get("status")=="success":
                self.username = resp.get("username")
                self.running = True
                threading.Thread(target=self.listen_server, daemon=True).start()
                self.show_chat()
            else:
                messagebox.showerror("Login Failed", resp.get("message","Invalid"))
                try:
                    self.sock.close()
                except:
                    pass
        except Exception as e:
            messagebox.showerror("Network", str(e))

    # ---------- Chat ----------
    def show_chat(self):
        self.clear()
        top_frame = tk.Frame(self.root, bg="#06121a")
        top_frame.pack(fill="x")
        tk.Label(top_frame, text=f"Logged in as: {self.username}", bg="#06121a", fg="#9be7d3", font=("Segoe UI", 11, "bold")).pack(side="left", padx=8, pady=6)

        main = tk.Frame(self.root, bg="#071226")
        main.pack(fill="both", expand=True, padx=8, pady=8)

        left = tk.Frame(main, bg="#0b2940", width=240)
        left.pack(side="left", fill="y")
        tk.Label(left, text="Select Recipient", bg="#0b2940", fg="#9be7d3", font=("Segoe UI", 12, "bold")).pack(fill="x", pady=6)
        self.recipient_var = tk.StringVar()
        self.recipient_combo = ttk.Combobox(left, textvariable=self.recipient_var, state="readonly", width=28)
        self.recipient_combo.pack(padx=8, pady=8)
        ttk.Button(left, text="Refresh", command=self.request_online).pack(padx=8, pady=6)
        ttk.Button(left, text="Logout", command=self.do_logout).pack(padx=8, pady=6)

        right = tk.Frame(main, bg="#04121a")
        right.pack(side="right", fill="both", expand=True)
        self.chat_text = tk.Text(right, bg="#071022", fg="white", font=("Segoe UI", 11), wrap="word")
        self.chat_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.chat_text.config(state="disabled")

        bottom = tk.Frame(self.root, bg="#06121a")
        bottom.pack(fill="x", pady=8)
        self.msg_var = tk.StringVar()
        self.entry = ttk.Entry(bottom, textvariable=self.msg_var, width=90)
        self.entry.pack(side="left", padx=8)
        self.entry.bind("<Return>", lambda e: self.send_message())
        ttk.Button(bottom, text="Send", command=self.send_message).pack(side="left", padx=6)

        # initial request for online users
        self.request_online()

    def request_online(self):
        try:
            send_json(self.sock, {"action":"get_online_users"})
        except:
            pass

    def send_message(self):
        recipient = self.recipient_var.get()
        if not recipient:
            messagebox.showwarning("Select recipient", "Please select a recipient from the dropdown")
            return
        text = self.msg_var.get().strip()
        if not text:
            return
        ts = datetime.now().strftime("%I:%M %p")
        try:
            send_json(self.sock, {"action":"send_message","from":self.username,"to":recipient,"message":text,"timestamp":ts})
            # locally display sent message
            self.display_message(self.username, text, ts)
            self.msg_var.set("")
        except Exception as e:
            messagebox.showerror("Send failed", str(e))

    def display_message(self, sender, text, timestamp):
        self.chat_text.config(state="normal")
        if sender == self.username:
            self.chat_text.insert("end", f"\nYou ({timestamp}): {text}\n")
        else:
            self.chat_text.insert("end", f"\n{sender} ({timestamp}): {text}\n")
        self.chat_text.config(state="disabled")
        self.chat_text.see("end")

    def do_logout(self):
        try:
            if self.username:
                send_json(self.sock, {"action":"logout","username":self.username})
        except:
            pass
        self.running = False
        try:
            self.sock.close()
        except:
            pass
        self.username = None
        self.show_main()

    # ---------- listen thread ----------
    def listen_server(self):
        buffer = ""
        while self.running:
            try:
                msgs, buffer = recv_jsons(self.sock, buffer)
                if msgs is None:
                    break
                for msg in msgs:
                    action = msg.get("action")
                    if action == "update_users":
                        users = msg.get("users", [])
                        others = [u for u in users if u != self.username]
                        # update combobox values on main thread
                        self.root.after(0, lambda vals=others: self._update_recipient_combo(vals))
                    elif action == "receive_message":
                        sender = msg.get("from")
                        text = msg.get("message")
                        ts = msg.get("timestamp", datetime.now().strftime("%I:%M %p"))
                        # ensure UI update on main thread
                        self.root.after(0, lambda s=sender, t=text, tm=ts: self.display_message(s, t, tm))
                    else:
                        pass
            except Exception:
                break
        self.running = False
        try:
            self.sock.close()
        except:
            pass

    def _update_recipient_combo(self, values):
        current = self.recipient_var.get()
        self.recipient_combo['values'] = values
        if current not in values:
            self.recipient_var.set("")

    def on_exit(self):
        try:
            if self.username:
                send_json(self.sock, {"action":"logout","username":self.username})
        except:
            pass
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClientGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_exit)
    root.mainloop()
