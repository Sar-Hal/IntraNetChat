import argparse
import socket
import threading
import tkinter as tk
from queue import Empty, Queue
from tkinter import messagebox, scrolledtext


class ChatClientUI:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.sock: socket.socket | None = None
        self.receiver_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.incoming: Queue[str] = Queue()

        self.root = tk.Tk()
        self.root.title("IntraNet Chat Client")
        self.root.geometry("760x520")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.host_var = tk.StringVar(value=self.host)
        self.port_var = tk.StringVar(value=str(self.port))
        self.nick_var = tk.StringVar()
        self.dm_target_var = tk.StringVar()
        self.message_var = tk.StringVar()
        self.dm_message_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Disconnected")

        self._build_ui()
        self.root.after(100, self.poll_incoming)

    def _build_ui(self) -> None:
        top = tk.Frame(self.root)
        top.pack(fill=tk.X, padx=10, pady=(10, 5))

        tk.Label(top, text="Host").pack(side=tk.LEFT)
        tk.Entry(top, textvariable=self.host_var, width=18).pack(side=tk.LEFT, padx=(5, 10))
        tk.Label(top, text="Port").pack(side=tk.LEFT)
        tk.Entry(top, textvariable=self.port_var, width=8).pack(side=tk.LEFT, padx=(5, 10))
        tk.Button(top, text="Connect", command=self.connect).pack(side=tk.LEFT)
        tk.Button(top, text="Disconnect", command=self.disconnect).pack(side=tk.LEFT, padx=(8, 0))
        tk.Label(top, textvariable=self.status_var).pack(side=tk.RIGHT)

        command_row = tk.Frame(self.root)
        command_row.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(command_row, text="Nick").pack(side=tk.LEFT)
        tk.Entry(command_row, textvariable=self.nick_var, width=16).pack(side=tk.LEFT, padx=(5, 5))
        tk.Button(command_row, text="Set Nick", command=self.set_nick).pack(side=tk.LEFT)
        tk.Button(command_row, text="List Users", command=self.list_users).pack(side=tk.LEFT, padx=(8, 0))
        tk.Button(command_row, text="Quit", command=self.quit_chat).pack(side=tk.LEFT, padx=(8, 0))

        self.chat_box = scrolledtext.ScrolledText(self.root, state=tk.DISABLED, wrap=tk.WORD)
        self.chat_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        public_row = tk.Frame(self.root)
        public_row.pack(fill=tk.X, padx=10, pady=(5, 3))
        tk.Label(public_row, text="Message").pack(side=tk.LEFT)
        public_entry = tk.Entry(public_row, textvariable=self.message_var)
        public_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 8))
        public_entry.bind("<Return>", lambda _event: self.send_public_message())
        tk.Button(public_row, text="Send", command=self.send_public_message).pack(side=tk.LEFT)

        dm_row = tk.Frame(self.root)
        dm_row.pack(fill=tk.X, padx=10, pady=(3, 10))
        tk.Label(dm_row, text="DM To").pack(side=tk.LEFT)
        tk.Entry(dm_row, textvariable=self.dm_target_var, width=14).pack(side=tk.LEFT, padx=(5, 8))
        tk.Label(dm_row, text="Text").pack(side=tk.LEFT)
        dm_entry = tk.Entry(dm_row, textvariable=self.dm_message_var)
        dm_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 8))
        dm_entry.bind("<Return>", lambda _event: self.send_dm())
        tk.Button(dm_row, text="Send DM", command=self.send_dm).pack(side=tk.LEFT)

    def append_chat(self, message: str) -> None:
        self.chat_box.configure(state=tk.NORMAL)
        self.chat_box.insert(tk.END, message + "\n")
        self.chat_box.see(tk.END)
        self.chat_box.configure(state=tk.DISABLED)

    def set_status(self, message: str) -> None:
        self.status_var.set(message)

    def is_connected(self) -> bool:
        return self.sock is not None and not self.stop_event.is_set()

    def send_line(self, line: str) -> None:
        if not self.sock:
            self.append_chat("[ERROR] Not connected.")
            return
        try:
            self.sock.sendall((line + "\n").encode("utf-8"))
        except OSError as err:
            self.append_chat(f"[ERROR] Send failed: {err}")
            self.disconnect()

    def connect(self) -> None:
        if self.is_connected():
            self.append_chat("[INFO] Already connected.")
            return

        host = self.host_var.get().strip()
        port_text = self.port_var.get().strip()
        if not host:
            messagebox.showerror("Connect", "Host is required.")
            return
        if not port_text.isdigit():
            messagebox.showerror("Connect", "Port must be a number.")
            return

        port = int(port_text)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((host, port))
        except OSError as err:
            messagebox.showerror("Connect", f"Could not connect to {host}:{port}\n{err}")
            try:
                sock.close()
            except OSError:
                pass
            return

        self.sock = sock
        self.stop_event.clear()
        self.receiver_thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.receiver_thread.start()
        self.append_chat(f"[INFO] Connected to {host}:{port}")
        self.set_status(f"Connected: {host}:{port}")

    def disconnect(self) -> None:
        sock = self.sock
        if sock is None:
            self.set_status("Disconnected")
            return

        self.stop_event.set()
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            sock.close()
        except OSError:
            pass

        self.sock = None
        self.set_status("Disconnected")

    def receive_loop(self) -> None:
        if self.sock is None:
            return

        buffer = ""
        while not self.stop_event.is_set():
            try:
                data = self.sock.recv(4096)
                if not data:
                    self.incoming.put("[INFO] Server disconnected.")
                    self.stop_event.set()
                    break

                buffer += data.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        self.incoming.put(line)
            except OSError:
                self.stop_event.set()
                break

    def poll_incoming(self) -> None:
        while True:
            try:
                message = self.incoming.get_nowait()
            except Empty:
                break
            self.append_chat(message)

        if self.sock is not None and self.stop_event.is_set():
            self.disconnect()

        self.root.after(100, self.poll_incoming)

    def set_nick(self) -> None:
        nick = self.nick_var.get().strip()
        if not nick:
            self.append_chat("[ERROR] Nickname cannot be empty.")
            return
        self.send_line(f"/nick {nick}")

    def list_users(self) -> None:
        self.send_line("/list")

    def send_public_message(self) -> None:
        message = self.message_var.get().strip()
        if not message:
            return
        self.send_line(message)
        self.message_var.set("")

    def send_dm(self) -> None:
        target = self.dm_target_var.get().strip()
        message = self.dm_message_var.get().strip()
        if not target or not message:
            self.append_chat("[ERROR] DM requires both target and message.")
            return
        self.send_line(f"/msg {target} {message}")
        self.dm_message_var.set("")

    def quit_chat(self) -> None:
        if self.sock is not None:
            self.send_line("/quit")
        self.disconnect()

    def on_close(self) -> None:
        self.quit_chat()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple LAN chat client (GUI)")
    parser.add_argument("--host", default="", help="Server IP address (optional, can connect from UI)")
    parser.add_argument("--port", type=int, default=9090, help="Server port (default: 9090)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = ChatClientUI(args.host, args.port)
    app.run()


if __name__ == "__main__":
    main()
