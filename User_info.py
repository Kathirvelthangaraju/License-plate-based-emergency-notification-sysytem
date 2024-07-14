from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
import random
from twilio.rest import Client

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Twilio credentials
account_sid = 'your twlio id'
auth_token = 'your twilio auth token'
twilio_phone_number = 'your twilio phone number'

# Create a Twilio client
twilio_client = Client(account_sid, auth_token)

def generate_otp():
    return str(random.randint(1000, 9999))

def create_table():
    conn = sqlite3.connect('user_info.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 name TEXT, license_plate TEXT, address TEXT, 
                 phone_number TEXT, emergency_phone_number TEXT, blood_group TEXT)''')
    conn.commit()
    conn.close()

def store_user_info(name, license_plate, address, phone_number, emergency_phone_number, blood_group):
    conn = sqlite3.connect('user_info.db')
    c = conn.cursor()
    c.execute('''INSERT INTO users (name, license_plate, address, phone_number, emergency_phone_number, blood_group) 
                 VALUES (?, ?, ?, ?, ?, ?)''', (name, license_plate, address, phone_number, emergency_phone_number, blood_group))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    license_plate = request.form.get('license_plate')
    address = request.form.get('address')
    phone_number = request.form.get('phone_number').strip()
    emergency_phone_number = request.form.get('emergency_phone_number').strip()
    blood_group = request.form.get('blood_group').strip()

    session['name'] = name
    session['license_plate'] = license_plate
    session['address'] = address
    session['phone_number'] = phone_number
    session['emergency_phone_number'] = emergency_phone_number
    session['blood_group'] = blood_group

    otp = generate_otp()
    session['otp'] = otp

    # Send OTP to the phone number
    message_body = f'Your OTP is: {otp}'
    twilio_client.messages.create(
        body=message_body,
        from_=twilio_phone_number,
        to=phone_number
    )

    return render_template('verify_otp.html')

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    user_otp = request.form.get('otp')
    if user_otp == session.get('otp'):
        name = session.get('name')
        license_plate = session.get('license_plate')
        address = session.get('address')
        phone_number = session.get('phone_number')
        emergency_phone_number = session.get('emergency_phone_number')
        blood_group = session.get('blood_group')
        store_user_info(name, license_plate, address, phone_number, emergency_phone_number, blood_group)
        session.clear()
        return render_template('thank_you.html')
    else:
        return "Invalid OTP"

if __name__ == '__main__':
    create_table()
    app.run(host='0.0.0.0', port=8080, debug=True)
