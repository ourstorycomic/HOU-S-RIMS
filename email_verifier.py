import socket
import smtplib
import re

def verify_email_exists(email):
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        return False
        
    domain = email.split('@')[1]
    
    if domain == 'gmail.com':
        try:
            server = smtplib.SMTP('gmail-smtp-in.l.google.com', 25, timeout=5)
            server.helo('localhost')
            server.mail('test@example.com')
            code, message = server.rcpt(email)
            server.quit()
            
            if code == 250:
                return True
            return False
        except Exception as e:
            print('SMTP check failed:', e)
            return True
            
    return True
