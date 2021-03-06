import json
import os
import requests


"""def send_email(receiver_email, subject, text):
    sender_email = os.getenv("MY_SENDER_EMAIL")  # Your website's official email address
    api_key = os.getenv('SENDGRID_API_KEY')

    if sender_email and api_key:
        url = "https://api.sendgrid.com/v3/mail/send"

        data = {"personalizations": [{
                    "to": [{"email": receiver_email}],
                    "subject": subject
                }],

                "from": {"email": sender_email},

                "content": [{
                    "type": "text/plain",
                    "value": text
                }]
        }

        headers = {
            'authorization': "Bearer {0}".format(api_key),
            'content-type': "application/json"
        }

        response = requests.request("POST", url=url, data=json.dumps(data), headers=headers)

        print("Sent to SendGrid")
        print(response.text)
    else:
        print("No env vars or no email address")"""

import os
from tasks import send_email_task


def send_email(receiver_email, subject, text):

    if os.getenv('REDIS_URL'):
        # if the web app is on Heroku, call the "send email" task
        send_email_task(receiver_email, subject, text)

    else:
        # but if you're on localhost, just simulate sending email in the console
        print("You are on localhost, so the email will not be really sent.")
        print("---------------EMAIL MESSAGE----------------")
        print("Email recipient: {}".format(receiver_email))
        print("Subject: {}".format(subject))
        print(text)
        print("---------------EMAIL MESSAGE----------------")