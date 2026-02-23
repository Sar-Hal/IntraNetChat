import argparse
import socket
import threading
from dataclasses import dataclass


@dataclass
class Client:
    conn: socket.socket
    addr: tuple[str, int]
    nick: str


class ChatServer:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients: dict[socket.socket, Client] = {}
        self.lock = threading.Lock()

    def start(self) -> None:
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(50)
        print(f"[SERVER] Listening on {self.host}:{self.port}")
        print("[SERVER] Commands: /nick <name>, /list, /msg <user> <text>, /quit")

        while True:
            conn, addr = self.server_socket.accept()
            thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
            thread.start()

    def send_line(self, conn: socket.socket, message: str) -> None:
        conn.sendall((message + "\n").encode("utf-8"))

    def broadcast(self, message: str, exclude: socket.socket | None = None) -> None:
        with self.lock:
            sockets = list(self.clients.keys())
        for sock in sockets:
            if sock is exclude:
                continue
            try:
                self.send_line(sock, message)
            except OSError:
                self.remove_client(sock)

    def remove_client(self, conn: socket.socket) -> None:
        with self.lock:
            client = self.clients.pop(conn, None)
        try:
            conn.close()
        except OSError:
            pass

        if client:
            self.broadcast(f"[INFO] {client.nick} left the chat.")
            print(f"[SERVER] Disconnected: {client.nick} {client.addr}")

    def set_nick(self, conn: socket.socket, new_nick: str) -> str:
        new_nick = new_nick.strip()
        if not new_nick:
            return "[ERROR] Nickname cannot be empty."
        if " " in new_nick:
            return "[ERROR] Nickname cannot contain spaces."

        with self.lock:
            if any(client.nick.lower() == new_nick.lower() for client in self.clients.values() if client.conn is not conn):
                return "[ERROR] Nickname already in use."
            current = self.clients.get(conn)
            if current is None:
                return "[ERROR] Client is not registered."
            old_nick = current.nick
            current.nick = new_nick

        self.broadcast(f"[INFO] {old_nick} is now known as {new_nick}.")
        return f"[OK] Your nickname is now {new_nick}."

    def list_users(self) -> str:
        with self.lock:
            names = sorted(client.nick for client in self.clients.values())
        return "[USERS] " + ", ".join(names)

    def private_message(self, sender_conn: socket.socket, target_nick: str, text: str) -> str:
        target_conn = None
        sender_nick = "unknown"

        with self.lock:
            sender = self.clients.get(sender_conn)
            if sender:
                sender_nick = sender.nick
            for conn, client in self.clients.items():
                if client.nick.lower() == target_nick.lower():
                    target_conn = conn
                    break

        if target_conn is None:
            return f"[ERROR] User '{target_nick}' not found."

        try:
            self.send_line(target_conn, f"[DM] {sender_nick}: {text}")
            return f"[OK] DM sent to {target_nick}."
        except OSError:
            self.remove_client(target_conn)
            return f"[ERROR] Failed to send DM to {target_nick}."

    def handle_command(self, conn: socket.socket, line: str) -> str | None:
        if line.startswith("/nick "):
            return self.set_nick(conn, line[6:].strip())

        if line == "/list":
            return self.list_users()

        if line.startswith("/msg "):
            parts = line.split(" ", 2)
            if len(parts) < 3:
                return "[ERROR] Usage: /msg <user> <text>"
            return self.private_message(conn, parts[1], parts[2])

        if line == "/quit":
            self.send_line(conn, "[INFO] Bye.")
            self.remove_client(conn)
            return None

        with self.lock:
            sender = self.clients.get(conn)
            sender_nick = sender.nick if sender else "unknown"

        self.broadcast(f"{sender_nick}: {line}", exclude=None)
        return None

    def handle_client(self, conn: socket.socket, addr: tuple[str, int]) -> None:
        nick = f"user{addr[1]}"
        with self.lock:
            self.clients[conn] = Client(conn=conn, addr=addr, nick=nick)

        print(f"[SERVER] Connected: {nick} {addr}")
        self.send_line(conn, f"[INFO] Connected as {nick}.")
        self.send_line(conn, "[INFO] Use /nick <name> to set your nickname.")
        self.broadcast(f"[INFO] {nick} joined the chat.", exclude=conn)

        buffer = ""
        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                buffer += data.decode("utf-8", errors="replace")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    response = self.handle_command(conn, line)
                    if response is not None:
                        self.send_line(conn, response)
        except OSError:
            pass
        finally:
            self.remove_client(conn)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple LAN chat server")
    parser.add_argument("--host", default="0.0.0.0", help="Host/IP to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=9090, help="Port to bind (default: 9090)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ChatServer(args.host, args.port)
    server.start()


if __name__ == "__main__":
    main()
