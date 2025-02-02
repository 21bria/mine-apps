from django.http import HttpResponse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
# def send_test_email(request):
#     sender_email   = "alpha.devp@gmail.com"
#     receiver_email = "brya.seran@gmail.com"
#     # password = "jpysplnnxhjkbhkf"  # App Password
#     password = "ngxmcvkglwlnkwsl"  # App Password

#     # Membuat pesan email
#     message = MIMEMultipart()
#     message["From"] = sender_email
#     message["To"] = receiver_email
#     message["Subject"] = "Test Email Subject"
#     body = "This is a test email."
#     message.attach(MIMEText(body, "plain"))

#     try:
#         # Menghubungkan ke server SMTP Gmail
#         # server = smtplib.SMTP("smtp.gmail.com", 587)
#         server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
#         # server.starttls()  # Enable TLS
#         server.login(sender_email, password)
#         server.sendmail(sender_email, receiver_email, message.as_string())
#         return HttpResponse("Email sent successfully")
#     except Exception as e:
#         return HttpResponse(f"Error: {e}")
#     finally:
#         server.quit()

# def send_test_email(request, sender_alias=None):
#     # Render konten HTML dari template
#     html_content = render_to_string('email_template.html', {
#         'username': 'John Doe',
#         'activation_link': 'https://example.com/activate-account/12345',
#     })

#     # Gunakan alias jika diberikan, atau fallback ke DEFAULT_FROM_EMAIL
#     sender_alias = sender_alias or "Alpha Notifications"
#     sender_email = f"{sender_alias} <{settings.EMAIL_HOST_USER}>"

#     subject = 'Test Email Subject'
#     recipient_list = ['meinardus.bria@scmnickel.com', 'brya.seran@gmail.com']

#     try:
#         # Buat objek EmailMessage
#         email = EmailMessage(
#             subject=subject,
#             body=html_content,
#             from_email=sender_email,
#             to=recipient_list,
#         )
#         email.content_subtype = "html"  # Mengatur konten sebagai HTML
#         email.send(fail_silently=False)
#         return HttpResponse("Email sent successfully")
#     except Exception as e:
#         return HttpResponse(f"Error: {e}")
        
# def send_test_email(request,sender_alias=None):
#     html_content = render_to_string('email_template.html', {
#         'username' : 'John Doe',
#         'activation_link': 'https://example.com/activate-account/12345'
#     })

#     # Gunakan alias jika diberikan, atau fallback ke DEFAULT_FROM_EMAIL
#     sender_alias = sender_alias or "Alpha Notifications"
#     sender_email = f"{sender_alias} <{settings.EMAIL_HOST_USER}>"

#     #  Gunakan alias jika diberikan, atau fallback ke DEFAULT_FROM_EMAIL
#     # sender_email = f"{sender_alias} <{settings.EMAIL_HOST_USER}>" if sender_alias else settings.DEFAULT_FROM_EMAIL

#     subject         = 'Test Email Subject'
#     # message         = 'This is a test email.'
#     message         = html_content
#     # from_email      = 'Awesome <alpha.dev@gmail.com>'  # Alias aktif
#     from_email      =  sender_email  # Alias pengirim
#     recipient_list  = ['meinardus.bria@scmnickel.com','brya.seran@gmail.com']

#     try:
#         # Mengirim email
#         send_mail(subject, message, from_email, recipient_list, fail_silently=False)
#         return HttpResponse("Email sent successfully")
#     except Exception as e:
#         return HttpResponse(f"Error: {e}")

# def send_test_email(request, sender_alias=None):
#     # Gunakan alias pengirim jika ada
#     sender_alias = sender_alias or "Alpha Notifications"
#     from_email = f"{sender_alias} <{settings.EMAIL_HOST_USER}>"

#     subject = 'Test Email Subject'
#     recipient_list = ['meinardus.bria@scmnickel.com', 'brya.seran@gmail.com']
#     message = f"""
#                 Hello,

#                 The workflow '' has been rejected by {request.user.username}.
#                 Please log in to review it.

#                 Thank you,
#                 Alpha System
#             """
#     try:
#         # Kirim email
#         # email.send(fail_silently=False)
#         send_mail(subject, message, from_email, recipient_list, fail_silently=False)
#         return HttpResponse("Email sent successfully")
#     except Exception as e:
#         return HttpResponse(f"Error: {e}")

def send_test_email(request, sender_alias=None):
    # Render konten HTML untuk email
    html_content = f"""
         <html>
            <body>
                <p style="margin-top: 20px;"><strong>Hello,</strong></p> <!-- Menambahkan margin atas untuk jarak -->
                <p>The workflow '' has been rejected by <strong>{request.user.username}</strong>.</p>
                <p>Please log in to review it.</p>
                <br>
                <p>Thank you,<br> Alpha System</p>
            </body>
        </html>
    """

    # Gunakan alias pengirim jika ada
    sender_alias = sender_alias or "Alpha Notifications"
    from_email = f"{sender_alias} <{settings.EMAIL_HOST_USER}>"

    subject = 'Test Email Subject'  # Subjek tetap teks biasa
    recipient_list = ['meinardus.bria@scmnickel.com', 'brya.seran@gmail.com']

    # Gunakan EmailMultiAlternatives untuk mengirimkan HTML
    email = EmailMultiAlternatives(subject, "This is the plain text version", from_email, recipient_list)
    
    # Lampirkan konten HTML
    email.attach_alternative(html_content, "text/html")

    try:
        # Kirim email
        email.send(fail_silently=False)
        return HttpResponse("Email sent successfully")
    except Exception as e:
        return HttpResponse(f"Error: {e}")