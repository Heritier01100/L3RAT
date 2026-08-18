# Android Remote Control Tool

**Legitimate Remote Device Management for Android**

A Python-launched Flask/Socket.IO web application for managing and monitoring registered Android devices.

> **Important:** This README documents the functionality that is actually present in the supplied `README.md`, `start_server.py`, and `app.py`. The current server does **not** contain a real Android APK implementation; its APK endpoint creates a placeholder file.

## ⚠️ Legal and Privacy Notice

This project is intended for:

- Managing your own devices
- Managing devices with explicit user consent
- Authorized testing and educational use

Do not use the software for unauthorized monitoring, surveillance, credential theft, or other illegal activity. Users are responsible for complying with applicable laws and obtaining any required consent.

---

## ✨ Current Features

| Feature | Current implementation |
|---|---|
| 🔐 Web login | Admin credentials are generated when the Flask server starts |
| 📊 Dashboard | `/` displays the login page or dashboard template depending on session state |
| 📱 Device registry | Devices are stored in SQLite |
| 🟢 Online devices | Socket.IO registration marks devices as online |
| ⚫ Offline devices | Socket.IO disconnect handling marks devices as offline |
| ❤️ Device heartbeat | Connected devices can update `last_seen`, battery, and location |
| 📍 Location data | The server stores location data received from a device heartbeat |
| 📡 Commands | Authenticated dashboard requests can send a command to a connected device |
| 📦 Create APK | Currently creates a **placeholder** `RemoteControl.apk`; it is not a functional Android APK |
| 📝 Command logging | Commands sent through the API are stored in SQLite |

The original project description lists camera, audio, vibration, screen control, and APK creation as intended features. The supplied `app.py`, however, does not implement the Android-side functionality for those operations. The command endpoint only forwards a command and optional parameters to a connected Socket.IO client.

---

# 🚀 Quick Start

## 1. Clone the repository

```bash
git clone https://github.com/Heritier01100/L3RAT.git
cd L3RAT
```

## 2. Create a virtual environment

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows PowerShell

```powershell
python -m venv venv
.env\Scripts\Activate.ps1
```

## 3. Install dependencies

The launcher expects the server dependencies to be listed in:

```text
server/requirements.txt
```

Install them manually with:

```bash
python3 -m pip install -r server/requirements.txt
```

On Windows:

```powershell
python -m pip install -r server/requirements.txt
```

## 4. Start the server

From the repository root:

```bash
python3 start_server.py
```

On Windows:

```powershell
python start_server.py
```

The launcher:

1. Checks whether Python is available.
2. Checks for `server/app.py`.
3. Installs packages from `server/requirements.txt`.
4. Changes into the `server` directory.
5. Opens the local dashboard in a browser after a short delay.
6. Starts `app.py`.

The supplied launcher reports the dashboard as:

```text
http://localhost:5000
```

It also prints the generated administrator credentials in the terminal.

---

# 🔐 Authentication

When `app.py` starts, it generates:

- An 8-character lowercase administrator username
- A 12-character alphanumeric administrator password

The credentials are printed to the terminal and written to:

```text
credentials.txt
```

The login endpoint compares the submitted username and password with these generated values.

### Do not commit credentials

Add the following to `.gitignore`:

```gitignore
credentials.txt
devices.db
*.pyc
__pycache__/
venv/
.env
```

The supplied credentials file contains generated credentials and should not be uploaded publicly.

---

# 🖥️ Dashboard

The root route is:

```text
/
```

If the user is not authenticated, the application renders:

```text
templates/login.html
```

After successful login, it renders:

```text
templates/dashboard.html
```

The application uses a Flask session to keep track of whether the administrator is logged in.

---

# 📱 Device Database

The application creates an SQLite database named:

```text
devices.db
```

The `devices` table stores:

| Field | Purpose |
|---|---|
| `device_id` | Unique device identifier |
| `device_name` | Device display name |
| `model` | Device model |
| `android_version` | Android version |
| `registered_at` | Registration timestamp |
| `last_seen` | Most recent heartbeat |
| `status` | Device status |
| `location` | JSON location data |
| `battery_level` | Battery level |
| `ip_address` | Stored IP address |

The application also creates a `command_log` table containing:

| Field | Purpose |
|---|---|
| `id` | Log record ID |
| `device_id` | Target device |
| `command` | Command name |
| `params` | Command parameters |
| `status` | Command status |
| `executed_at` | Execution timestamp |

---

# 🟢 Online and ⚫ Offline Devices

The application maintains an in-memory mapping:

```python
active_devices = {}
```

When a device registers through Socket.IO, its device ID is associated with its Socket.IO session ID.

The device is then stored in SQLite with:

```text
status = online
```

When the Socket.IO connection disconnects, the application removes the device from the active-device mapping and updates its database status to:

```text
status = offline
```

---

# ❤️ Device Heartbeat

Connected clients can send a `device_heartbeat` Socket.IO event.

The heartbeat can contain:

```text
device_id
battery
location
```

The server updates:

```text
last_seen
status
battery_level
location
```

The status is set to:

```text
online
```

when a valid active device sends a heartbeat.

---

# 📡 API Endpoints

## `GET /`

Displays either the login page or dashboard.

Authentication is required to access the dashboard.

---

## `POST /login`

Authenticates the administrator.

Example request:

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

Successful authentication creates a logged-in Flask session.

---

## `GET /logout`

Clears the current Flask session.

---

## `GET /api/devices`

Returns registered devices.

Authentication is required.

The response contains information such as:

```json
{
  "device_id": "example-device",
  "device_name": "Android Device",
  "model": "Unknown",
  "android_version": "Unknown",
  "registered_at": "...",
  "last_seen": "...",
  "status": "online",
  "location": null,
  "battery_level": 0,
  "ip_address": "0.0.0.0"
}
```

---

## `POST /api/device/<device_id>/command`

Sends a command to an active Socket.IO device.

Authentication is required.

The request can contain:

```json
{
  "command": "example_command",
  "params": {}
}
```

If the device is currently active, the server emits a Socket.IO `command` event containing the command and parameters.

The command is also recorded in the SQLite `command_log` table.

> The supplied server does not define the Android-side behavior for individual commands. A connected client must implement its own authorized handling.

---

## `POST /api/create_apk`

Authentication is required.

### Current behavior

This endpoint does **not** build a real Android APK.

It creates:

```text
RemoteControl.apk
```

as a plain text placeholder containing information that a real APK must be built separately with Android Studio.

Therefore, the current `Create APK` feature should be considered a **placeholder**, not an APK builder.

---

# 🔌 Socket.IO Events

The server defines the following Socket.IO events.

## `connect`

Triggered when a Socket.IO client connects.

The server prints the client's Socket.IO session ID.

---

## `device_register`

A client can send:

```json
{
  "device_id": "device-id",
  "device_name": "Android Device"
}
```

The server:

1. Adds the device to `active_devices`.
2. Inserts or replaces its database record.
3. Sets its status to `online`.
4. Emits `registration_success`.
5. Broadcasts `device_online`.

---

## `device_heartbeat`

A client can send heartbeat information including:

```json
{
  "device_id": "device-id",
  "battery": 75,
  "location": {
    "latitude": 0,
    "longitude": 0
  }
}
```

The server updates the device's heartbeat information.

---

## `disconnect`

When a Socket.IO client disconnects, the server searches for the associated device and changes its status to:

```text
offline
```

It also broadcasts a `device_offline` event.

---

# 🏗️ Current Architecture

```text
                    Browser
                       │
                       ▼
              ┌─────────────────┐
              │  Flask Dashboard │
              │    Login/UI      │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   Flask Server   │
              │   REST + Socket  │
              └───────┬─────────┘
                      │
             ┌────────┴────────┐
             ▼                 ▼
       ┌───────────┐     ┌──────────────┐
       │  SQLite   │     │ Socket.IO    │
       │ devices.db│     │ active client│
       └───────────┘     └──────────────┘
```

---

# 📂 Project Structure

The supplied launcher expects this structure at minimum:

```text
L3RAT/
├── README.md
├── start_server.py
└── server/
    ├── app.py
    └── requirements.txt
```

The Flask application also expects the relevant template files used by:

```python
render_template('login.html')
render_template('dashboard.html')
```

A typical project can therefore contain:

```text
L3RAT/
├── README.md
├── start_server.py
├── server/
│   ├── app.py
│   ├── requirements.txt
│   ├── templates/
│   │   ├── login.html
│   │   └── dashboard.html
│   ├── devices.db
│   └── credentials.txt
└── android/
    └── ...
```

Generated files such as `devices.db` and `credentials.txt` should normally remain outside Git.

---

# 🔧 Launcher Workflow

`start_server.py` is the entry point supplied with the project.

Its workflow is:

```text
python start_server.py
        │
        ▼
Check Python
        │
        ▼
Check server/app.py
        │
        ▼
Install server/requirements.txt
        │
        ▼
Change directory to server/
        │
        ▼
Open http://localhost:5000
        │
        ▼
Run app.py
```

Press:

```text
Ctrl + C
```

to stop the server.

---

# ⚠️ Current Limitations

The supplied files do **not** implement all of the features described in the original project description.

### APK creation

Currently creates a text placeholder rather than a functional APK.

### Camera

No camera implementation is present in `app.py`.

### Audio

No microphone/audio implementation is present in `app.py`.

### Vibration

No vibration implementation is present in `app.py`.

### Screen control

The server can forward an arbitrary command to a connected Socket.IO client, but the supplied files do not contain an Android implementation that performs screen control.

### Android application

No Android client source was supplied with the files analyzed for this README.

Therefore, these capabilities should not be described as fully implemented until an authorized Android client implementing them actually exists.

---

# 🔒 Security Considerations

The current code is suitable for local development but should not be treated as a production-ready remote management server.

Important areas requiring improvement include:

- Device authentication
- Secure device pairing
- Restricted CORS configuration
- HTTPS/TLS
- Secure credential storage
- Session security
- CSRF protection
- Rate limiting
- Authorization for individual devices
- Secure command validation
- Input validation
- Audit logging
- Secret management

The current application uses:

```python
CORS(app)
```

and:

```python
SocketIO(app, cors_allowed_origins="*")
```

which are broad configurations and should be restricted before deployment.

The server also binds to:

```text
0.0.0.0:5000
```

so it is not strictly limited to loopback networking. For local-only development, binding specifically to `127.0.0.1` is safer.

---

# 🧪 Development

Start the application:

```bash
python3 start_server.py
```

Then open:

```text
http://localhost:5000
```

Use the administrator credentials printed by the server.

For debugging the Python application directly:

```bash
cd server
python3 app.py
```

---

# 👤 Author

**Heritier01100**

GitHub:

https://github.com/Heritier01100

Repository:

https://github.com/Heritier01100/L3RAT

---

# 📄 License

No license was specified in the supplied files.

Add an appropriate open-source license before distributing the project publicly.

---

# ⚠️ Disclaimer

This project is documented as a device-management and remote-support application.

Use it only on devices you own or devices for which you have explicit authorization. Users are responsible for obtaining required consent, protecting credentials, and complying with applicable laws and platform policies.
