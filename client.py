import argparse
import socket
import sys
import threading


def receive_loop(sock: socket.socket, stop_event: threading.Event) -> None:
    buffer = ""
    while not stop_event.is_set():
        try:
            data = sock.recv(4096)
            if not data:
                print("\n[INFO] Server disconnected.")
                stop_event.set()
                break

            buffer += data.decode("utf-8", errors="replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                print(f"\n{line}", flush=True)
        except OSError:
            stop_event.set()
            break


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple LAN chat client")
    parser.add_argument("--host", required=True, help="Server IP address")
    parser.add_argument("--port", type=int, default=9090, help="Server port (default: 9090)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((args.host, args.port))
    except OSError as err:
        print(f"[ERROR] Could not connect to {args.host}:{args.port} - {err}")
        sys.exit(1)

    print(f"[INFO] Connected to {args.host}:{args.port}")
    print("[INFO] Commands: /nick <name>, /list, /msg <user> <text>, /quit, /shutdown")

    stop_event = threading.Event()
    receiver = threading.Thread(target=receive_loop, args=(sock, stop_event), daemon=True)
    receiver.start()

    try:
        while not stop_event.is_set():
            line = input("> ").strip()
            if not line:
                continue

            sock.sendall((line + "\n").encode("utf-8"))
            if line == "/quit":
                stop_event.set()
                break
    except (KeyboardInterrupt, EOFError):
        try:
            sock.sendall(b"/quit\n")
        except OSError:
            pass
    finally:
        stop_event.set()
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        sock.close()


if __name__ == "__main__":
    main()
