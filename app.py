from flask import Flask, request, jsonify, render_template, current_app
import mysql.connector
from datetime import datetime, timedelta
import serial
import json
from threading import Thread

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Setup Serial Connection
ser = serial.Serial('COM7', 9600, timeout=1)
ser.flush()

current_parking_status = {}

# Database connection configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'smart_parking'
}

def connect_db():
    conn = mysql.connector.connect(**db_config)
    return conn

def handle_serial_data(data):
    try:
        type = data['type']
        status = data['status']
        rfid_tag = data['rfidTag']
        distance = data['distance']
        slot_id = data['slotID']
    
        if type == 'RFID':
            verify_and_act_on_rfid(rfid_tag)
            pass
        elif type == 'Parking':
            handle_parking_event(slot_id, status, distance)
            pass
        elif type == 'Gate':
            handle_gate_event('13851605', 'exit' if status == 1 else 'enter')
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")


def verify_and_act_on_rfid(rfid_tag):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    print(f"Verifying RFID: {rfid_tag}")
    try:
        cursor.execute("SELECT user_id FROM users WHERE rfid_tag = %s", (rfid_tag,))
        user = cursor.fetchone()
        print(f"User: {user}")
        if user:
            open_gate_rfid()
            # RFID is registered, open gate and log access as successful
            cursor.execute("INSERT INTO access_logs (user_id, event_type, timestamp) VALUES (%s, %s, %s)", (user['user_id'], 'enter', datetime.now()))
        else:
            # RFID not registered, do not open gate and log access as denied
            cursor.execute("INSERT INTO system_alarms (type, description) VALUES (%s, %s)", ('Error at gate', 'Unregistered RFID detected'))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def open_gate_rfid():
    ser.write(b'OPEN_GATE\n')


def handle_parking_event(slot_id, status, distance):
    current_status = current_parking_status.get(slot_id, None)
    if status == 0 and current_status == 1:
        end_parking_session(slot_id)
    elif status == 1 and current_status != 1:
        start_parking_session(slot_id)
    elif status == 2:
        log_system_alarm(slot_id, "Error at parking slot", "Parking sensor error detected")
    current_parking_status[slot_id] = status


def start_parking_session(slot_id):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO parking_sessions (slot_id, start_time, status) VALUES (%s, %s, %s)', (slot_id, datetime.now(), 'active'))
        cursor.execute('UPDATE parking_slots SET slot_status = 1 WHERE slot_id = %s', (slot_id,))
        conn.commit()
    except Exception as e:
        print(f"Error starting parking session: {e}")
    finally:
        cursor.close()
        conn.close()


def end_parking_session(slot_id):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE parking_sessions SET end_time = %s, status = %s WHERE slot_id = %s AND end_time IS NULL', (datetime.now(), 'completed', slot_id))
        cursor.execute('UPDATE parking_slots SET slot_status = 0 WHERE slot_id = %s', (slot_id,))
        conn.commit()
    except Exception as e:
        print(f"Error ending parking session: {e}")
    finally:
        cursor.close()
        conn.close()


def log_system_alarm(slot_id, alarm_type, description):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO system_alarms (type, description, timestamp) VALUES (%s, %s, %s)', (alarm_type, description, datetime.now()))
        conn.commit()
    except Exception as e:
        print(f"Error logging system alarm: {e}")
    finally:
        cursor.close()
        conn.close()


def handle_gate_event(rfid_tag, event_type):
    user_id = get_user_id_by_rfid(rfid_tag)
    if user_id:
        execute_db_query(
            'INSERT INTO access_logs (user_id, event_type, timestamp) VALUES (%s, %s, %s)',
            (user_id, event_type, datetime.now())
        )


def get_user_id_by_rfid(rfid_tag):
    return execute_db_query(
        'SELECT user_id FROM users WHERE rfid_tag = %s', 
        (rfid_tag,), 
        fetchone=True
    )


def execute_db_query(query, params=None, fetchone=False):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            if fetchone:
                return cursor.fetchone()[0]
            conn.commit()


def serial_thread():
    while True:
        line = ser.readline().decode('utf-8').strip()
        if line:
            try:
                data = json.loads(line) 
                handle_serial_data(data)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e} - Line: {line}")

def start_serial_thread():
    thread = Thread(target=serial_thread)
    thread.daemon = True
    thread.start()



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/data', methods=['GET'])
def api_data():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch recent parking sessions
        cursor.execute('''
            SELECT ps.session_id, ps.slot_id, ps.start_time, ps.end_time, ps.status
            FROM parking_sessions ps
            ORDER BY ps.start_time DESC
            LIMIT 10
        ''')
        recent_sessions = cursor.fetchall()

        # Fetch current slot occupancy
        cursor.execute('''
            SELECT 
                s.slot_id, 
                CASE 
                    WHEN s.slot_status = 1 THEN 'Occupied' 
                    ELSE 'Available' 
                END AS occupancy_status
            FROM parking_slots s;
        ''')
        current_occupancy = cursor.fetchall()
        
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Unable to retrieve data"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({
        'recent_sessions': recent_sessions,
        'current_occupancy': current_occupancy,
    })


@app.route('/api/occupancy_stats', methods=['GET'])
def occupancy_stats():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Today's stats
        cursor.execute('''
            SELECT ps.slot_id, SUM(TIMESTAMPDIFF(MINUTE, ps.start_time, COALESCE(ps.end_time, NOW()))) AS total_minutes_today
            FROM parking_sessions ps
            WHERE DATE(ps.start_time) = CURDATE()
            GROUP BY ps.slot_id;
        ''')
        today_stats = cursor.fetchall()

        # This week's stats
        cursor.execute('''
            SELECT ps.slot_id, SUM(TIMESTAMPDIFF(MINUTE, ps.start_time, COALESCE(ps.end_time, NOW()))) AS total_minutes_week
            FROM parking_sessions ps
            WHERE YEARWEEK(ps.start_time, 1) = YEARWEEK(CURDATE(), 1)
            GROUP BY ps.slot_id;
        ''')
        week_stats = cursor.fetchall()

        # This month's stats
        cursor.execute('''
            SELECT ps.slot_id, SUM(TIMESTAMPDIFF(MINUTE, ps.start_time, COALESCE(ps.end_time, NOW()))) AS total_minutes_month
            FROM parking_sessions ps
            WHERE MONTH(ps.start_time) = MONTH(CURDATE()) AND YEAR(ps.start_time) = YEAR(CURDATE())
            GROUP BY ps.slot_id;
        ''')
        month_stats = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return jsonify({
        'today_stats': today_stats,
        'week_stats': week_stats,
        'month_stats': month_stats
    })


@app.route('/api/open_gate', methods=['POST'])
def open_gate():
    with current_app.app_context():
        ser.write(b'OPEN_GATE\n')
        return jsonify({'status': 'Gate opened'})


@app.route('/api/access_logs', methods=['GET'])
def get_access_logs():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT log_id, user_id, event_type, timestamp
            FROM access_logs
            ORDER BY timestamp DESC
        ''')
        logs = cursor.fetchall()
        return jsonify(logs)
    except Exception as e:
        print(f"Error fetching access logs: {e}")
        return jsonify([]), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/system_alarms', methods=['GET'])
def get_system_alarms():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT alarm_id, type, description, timestamp
            FROM system_alarms
            ORDER BY timestamp DESC
        ''')
        alarms = cursor.fetchall()
        return jsonify(alarms)
    except Exception as e:
        print(f"Error fetching system alarms: {e}")
        return jsonify([]), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/manage_users', methods=['POST'])
def manage_users():
    user_id = request.json.get('user_id')
    action = request.json.get('action')
    conn = connect_db()
    cursor = conn.cursor()
    if action == 'delete':
        cursor.execute('DELETE FROM users WHERE user_id = %s', (user_id,))
    elif action == 'add':
        username = request.json.get('username')
        rfid_tag = request.json.get('rfid_tag')
        email = request.json.get('email')
        cursor.execute('INSERT INTO users (username, email, rfid_tag, created_at) VALUES (%s, %s, %s, %s)', (username, email, rfid_tag, datetime.now())) 
    elif action == 'edit':
        new_username = request.json.get('new_username')
        cursor.execute('UPDATE users SET username = %s WHERE user_id = %s', (new_username, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'status': 'Success'})


@app.route('/api/get_registered_users', methods=['GET'])
def get_registered_users():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT user_id, username, email, rfid_tag FROM users')
    registered_users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(registered_users)


if __name__ == 'app':
    print("Starting server...")
    start_serial_thread()
    print("Serial thread started...")
    app.run(host='0.0.0.0', port=5000, debug=True)
    print("Flask app is running...")
