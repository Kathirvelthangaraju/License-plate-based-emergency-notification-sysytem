from flask import Flask, render_template, request, redirect, url_for
import os
import sqlite3
import pytesseract
import cv2
import imutils
import numpy as np
import pandas as pd
import time


from twilio.rest import Client

app = Flask(__name__)

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DATABASE = 'user_info.db'

# Your Twilio account SID, Auth Token, and Twilio phone number
account_sid = 'your twlio id'
auth_token = 'your twilio auth token'
twilio_phone_number = 'your twilio phone number'

# Create a Twilio client
twilio_client = Client(account_sid, auth_token)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image(image_path):
    # Load the image
    image = cv2.imread(image_path)
    image = imutils.resize(image, width=500)

    # Preprocessing steps ...
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)

    edged = cv2.Canny(gray, 170, 200)
    (cnts, _) = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:30]
    NumberPlateCnt = None

    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            NumberPlateCnt = approx
            break

    # Masking the part other than the number plate
    mask = np.zeros(gray.shape, np.uint8)
    new_image = cv2.drawContours(mask, [NumberPlateCnt], 0, 255, -1)
    new_image = cv2.bitwise_and(image, image, mask=mask)

    # OCR processing
    config = ('-l eng --oem 1 --psm 3')
    text = pytesseract.image_to_string(new_image, config=config)

    # Remove leading and trailing whitespaces from the recognized text
    text = text.strip()

    return text

def retrieve_user_info(plate_number):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id,name,license_plate,address,phone_number,emergency_phone_number,blood_group FROM users WHERE license_plate = ?", (plate_number,))
    result = c.fetchone()
    conn.close()
    return result if result else None



def send_sms(to_phone_number,user_info, recognized_text):
    # Your message
    #name = user_info[1] if user_info else "Unknown"
    license_plate = recognized_text if recognized_text else "Unknown"
    message_body = f'Emergency,{recognized_text},please contact near by police station immediately' \
                   f'அவசரநிலை, உடனடியாக அருகிலுள்ள காவல் நிலையத்தைத் தொடர்பு கொள்ளவும்'
    print(to_phone_number)

    # Send the SMS
    message = twilio_client.messages.create(
        body=message_body,
        from_=twilio_phone_number,
        to=to_phone_number
    )

    print(f"Message sent successfully! SID: {message.sid}")

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    user_info = None
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            recognized_text = process_image(filename)
            user_info = retrieve_user_info(recognized_text)
            if user_info:
                send_sms(user_info[5], user_info[1], recognized_text)  # Passing name and recognized text to send_sms
            return render_template('result.html', text=recognized_text, user_info=user_info)
    return render_template('upload.html')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)
