# Chat Application

## Description
The Chat Application is a real-time messaging platform built using Python, Socket Programming, Tkinter GUI, and SQLite3.  
It allows multiple or more clients to connect to a central server and exchange private messages securely.

---

## Features
- 🔒 Private messaging (choose recipient from dropdown)
- 👤 User registration & login (phone, username, password)
- 🖤 Modern dark-mode Tkinter interface
- 🗂️ Automatic creation of `users.db` SQLite database
- 👥 View registered users via `viewusers.py`

---

## How to Run
📜 Fistly create folder and open into VS code.

📜 build server01.py ,client01.py ,viewusers01.py files into folder.

📜 open folder into the file explorer and right click go to terminal.

📜 now following below instructions 
1. **Start the server**
   ```bash
    python server01.py
2. Start one or more clients
   ```bash
    python client01.py
3. Register and Login using your details.
4. Two more clients necessary for client to client chat.
    
6. After logging in:
    * Select a recipient from the dropdown.
    * Type your message.
    * Click Send to deliver a private message.
7. (Optional) View all registered users
   ```bash
    python viewusers01.py

## Requirements
  * Python 3.x
  * Tkinter (comes pre-installed with Python)
  * SQLite3 (built-in with Python)

## Notes
  * This is a local network chat app for learning and testing.
  * For production use, consider adding:
     > Password hashing (bcrypt or hashlib)
     
     > SSL/TLS encryption for sockets
     
     > Better exception handling and logging
 
## Folder Structure
   ```bash
    SecureChatApp/
     ├── server.py
     ├── client.py
     ├── viewusers.py
     ├── users.db        # Automatically created after first run
     └── README.md

     
      



