# client_main.py
import tkinter as tk
from client_core import ChatClient

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()
