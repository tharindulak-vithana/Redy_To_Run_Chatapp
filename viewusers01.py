# viewusers.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

DB_FILE = "users.db"
POLL_MS = 3000

class ViewUsersApp:
    def __init__(self, root):
        self.root = root
        root.title("Registered Users - Admin")
        root.geometry("820x520")
        root.configure(bg="#071226")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background="#1abc9c", foreground="white")
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 11))

        ttk.Label(root, text="Registered Users", font=("Segoe UI", 18, "bold"), background="#071226", foreground="#9be7d3").pack(fill="x", pady=8)

        frame = tk.Frame(root, bg="#06121a")
        frame.pack(fill="both", expand=True, padx=12, pady=8)

        columns = ("phone", "username", "password")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        self.tree.heading("phone", text="📞 Phone (with country code)")
        self.tree.heading("username", text="👤 Username")
        self.tree.heading("password", text="🔑 Password")
        self.tree.column("phone", width=300, anchor="center")
        self.tree.column("username", width=250, anchor="center")
        self.tree.column("password", width=250, anchor="center")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        btnf = tk.Frame(root, bg="#071226")
        btnf.pack(pady=10)
        ttk.Button(btnf, text="🔄 Refresh", command=self.load_users).grid(row=0, column=0, padx=8)
        ttk.Button(btnf, text="🗑 Delete Selected", command=self.delete_selected).grid(row=0, column=1, padx=8)
        ttk.Button(btnf, text="❌ Exit", command=root.destroy).grid(row=0, column=2, padx=8)

        self.load_users()
        self._poll()

    def load_users(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        try:
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("SELECT country, phone, username, password FROM users ORDER BY username COLLATE NOCASE")
            rows = cur.fetchall()
            for r in rows:
                phone_display = (r[0] + " " + r[1]).strip()
                self.tree.insert("", "end", values=(phone_display, r[2], r[3]))
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("DB Error", str(e))

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "No user selected")
            return
        item = self.tree.item(sel[0])
        username = item['values'][1]
        ok = messagebox.askyesno("Confirm", f"Delete user '{username}' ?")
        if not ok:
            return
        try:
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE username=?", (username,))
            conn.commit()
            conn.close()
            self.load_users()
            messagebox.showinfo("Deleted", f"User '{username}' removed")
        except sqlite3.Error as e:
            messagebox.showerror("DB Error", str(e))

    def _poll(self):
        try:
            self.load_users()
        finally:
            self.root.after(POLL_MS, self._poll)

if __name__ == "__main__":
    root = tk.Tk()
    app = ViewUsersApp(root)
    root.mainloop()
