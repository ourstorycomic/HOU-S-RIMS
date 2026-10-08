
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from email.mime.base import MIMEBase
from email import encoders

def send_notification_email(to_email, subject, content, html_content=None, attachment_paths=None):
    # Cấu hình email tại đây hoặc qua biến môi trường
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    
    # ĐIỀN EMAIL CỦA BẠN VÀO DÒNG BÊN DƯỚI
    SENDER_EMAIL = os.environ.get('MAIL_USERNAME', 'kastanland1169@gmail.com') 
    
    # Mật khẩu ứng dụng bạn vừa cấp (Xóa dấu cách đi)
    SENDER_PASSWORD = os.environ.get('MAIL_PASSWORD', 'sjvggmnrnygsfkxx') 
    
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print('Không thể gửi email: Chưa cấu hình MAIL_USERNAME đúng cách')
        return False
        
    try:
        # Create the root message (mixed is needed if we have attachments)
        msg = MIMEMultipart('mixed')
        msg['From'] = f"HOU S-RIMS <{SENDER_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Create the alternative part for text/html
        alt_part = MIMEMultipart('alternative')
        alt_part.attach(MIMEText(content, 'plain', 'utf-8'))
        if html_content:
            alt_part.attach(MIMEText(html_content, 'html', 'utf-8'))
            
        msg.attach(alt_part)
            
        # Attach files if provided
        if attachment_paths:
            if isinstance(attachment_paths, str):
                attachment_paths = [attachment_paths]
            for attachment_path in attachment_paths:
                if os.path.exists(attachment_path):
                    with open(attachment_path, "rb") as attachment:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    filename = os.path.basename(attachment_path)
                    part.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{filename}"',
                    )
                    msg.attach(part)
            
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f'Successfully sent email to {to_email}')
        return True
    except Exception as e:
        print(f'Error sending email: {e}')
        return False

import threading
def send_email_async(to_email, subject, content, html_content=None, attachment_paths=None):
    thread = threading.Thread(target=send_notification_email, args=(to_email, subject, content, html_content, attachment_paths))
    thread.daemon = True
    thread.start()

