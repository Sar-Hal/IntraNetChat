# Wi-Fi LAN Chat (Simple Prototype)

This is a lightweight messaging server/client you can run on the same local network (for example, your college Wi-Fi).

## Features

- Multi-user chat over TCP
- Nicknames (`/nick yourname`)
- Online users list (`/list`)
- Private message (`/msg username hello`)
- Exit command (`/quit`)
- Stop server command (`/shutdown`)

## Requirements

- Python 3.10+
- All devices must be on the same network and allowed to reach your laptop's port

## 1) Start server on your laptop

```bash
python server.py --host 0.0.0.0 --port 9090
```

Run from this repository folder (`IntraNetChat`).

## 2) Find your laptop IP

On Windows PowerShell:

```powershell
ipconfig
```

Use your Wi-Fi IPv4 address, for example `10.x.x.x` or `192.168.x.x`.

## 3) Allow inbound firewall rule (if needed)

Open Windows Defender Firewall and allow inbound TCP port `9090` for your current network profile.

## 4) Connect from each friend device

```bash
python client.py --host <YOUR_LAPTOP_IP> --port 9090
```

Examples after connecting:

```text
/nick lena
/list
/msg sam Hey, are you in class?
Hello everyone!
/shutdown
/quit
```

## Notes for college Wi-Fi

- Some campuses block peer-to-peer traffic (client-to-client/laptop ports). If your friends cannot connect, ask IT whether local LAN traffic is restricted.
- If blocked, deploy the server on a cloud VM/VPS and let everyone connect to that public IP.
- Do not send sensitive data: this prototype uses plain TCP (no encryption/auth).
