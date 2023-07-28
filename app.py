from flask import Flask, request, render_template, jsonify
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import cv2
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from twilio.rest import Client


now = datetime.now()
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

app = Flask(__name__)
model = load_model('/Users/damodargupta/Desktop/Omniscient/model/model_updated7.h5')

account_sid = 'enter your twilio sid'
auth_token = 'enter twilio auth token'

# Twilio phone numbers
from_number = 'enter twilio phone number'
to_number = 'enter your number'

# Create a Twilio client object
client = Client(account_sid, auth_token)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/predict', methods=['POST'])
def predict():
    file = request.files['file']
    filepath = os.path.join(file.filename)
    file.save(filepath)
    cap = cv2.VideoCapture(filepath)

    img_width, img_height = 224, 224

    classes = ['assault', 'normal']

    predictions = []

    while cap.isOpened():
        ret, frame = cap.read()

        if ret:
            frame = cv2.resize(frame, (img_width, img_height))
            x = image.img_to_array(frame)
            x = np.expand_dims(x, axis=0)
            x = x / 255.0

            prediction = model.predict(x)

            predicted_class = classes[np.argmax(prediction)]

            predictions.append(predicted_class)
        else:
            break
    cap.release()
    assault_count = predictions.count('assault')

    if assault_count > 0.9:
        result = 'Yes'
        subject = "Crime Detected"
        body = "Assault has been detected at \n Address : xyz,example stree,123 example apts,123456 \n Severity level : High \n at time :" + dt_string
        recipient = "enter your email id"
        send_email(subject, body, recipient, attachment_path=filepath)
        call = client.calls.create(
        twiml='<Response><Say>An assault has been detected at the location xyz,example street,123 example apts,123456 the severity level of the crime is high please take action immediately</Say></Response>',
        to=to_number,
        from_=from_number
        )
    else:
        result = 'No'

    return jsonify({'result': result})

def send_email(subject, body, recipient, attachment_path=None):
    sender_email = "omnisci3ntai@gmail.com"
    sender_password = "dxsivjrpblvnakbh"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    if attachment_path:
        filename = os.path.basename(attachment_path)
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {filename}",
        )
        message.attach(part)

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(sender_email, sender_password)
        smtp.send_message(message)

if __name__ == '__main__':
    app.run(debug=True)
