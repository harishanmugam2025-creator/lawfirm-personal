import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

sg = SendGridAPIClient('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')
message = Mail(
    from_email='ravanthsri20@gmail.com',
    to_emails='harishanmugam125@gmail.com',
    subject='Test',
    html_content='Test'
)
try:
    response = sg.send(message)
    print("Status Code:", response.status_code)
    print("Body:", response.body)
except Exception as e:
    print("Exception:", str(e))
    # if it has a body we can print it
    if hasattr(e, 'body'):
        print("Error body:", e.body)
