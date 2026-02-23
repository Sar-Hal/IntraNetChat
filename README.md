# IntraNetChat (Wi-Fi LAN Chat)

Simple local-network chat app for one host and multiple clients.

## Important model

- Only **one host** runs `server.py`.
- All other devices run `client.py` and connect to the host IP.
- Everyone must be on the same Wi-Fi network.

## Requirements

- Python 3.10+
- Devices must be allowed to reach host TCP port (default `9090`)

## Host setup (only one person does this)

### 1) Start the server

From this project folder:

```bash
python server.py --host 0.0.0.0 --port 9090
```

### 2) Find host IP address

On Windows PowerShell:

```powershell
ipconfig
```

Share the Wi-Fi IPv4 address (example: `10.x.x.x` or `192.168.x.x`) with clients.

### 3) Open firewall (if needed)

Allow inbound TCP `9090` in Windows Defender Firewall for your current network profile.

### 4) Stop the server

- In host terminal: `Ctrl + C`
- Or from any connected client: `/shutdown`

## Client setup (everyone else)

### Option A: Connect directly from command line

```bash
python client.py --host <HOST_IP> --port 9090
```

### Option B: Open GUI first, connect inside UI

```bash
python client.py
```

Then enter host and port in the app and click **Connect**.

## Client UI usage

- **Set nickname**: enter name in `Nick` and click **Set Nick**
- **Send public message**: type in `Message` and click **Send**
- **Send private message**: set `DM To` + `Text`, click **Send DM**
- **View users**: click **List Users**
- **Leave chat**: click **Quit**

## Protocol commands (supported by server)

- `/nick <name>`
- `/list`
- `/msg <user> <text>`
- `/quit`
- `/shutdown`

## Troubleshooting (college Wi-Fi)

- If clients cannot connect, campus Wi-Fi may block peer-to-peer LAN traffic.
- Verify host IP and port are correct.
- Verify firewall allows inbound port `9090`.
- If LAN is blocked, run server on a cloud VM/VPS and connect via public IP.

## Security note

This prototype uses plain TCP (no encryption/authentication). Do not share sensitive data.
