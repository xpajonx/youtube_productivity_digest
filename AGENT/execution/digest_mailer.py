import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from execution.config import configs, console

class DigestMailer:
    def __init__(self):
        # Hardcoded for Gmail as per user preference
        self.server = "smtp.gmail.com"
        self.port = 587
        # Simplified secrets
        self.user = os.getenv("GMAIL_USER")
        self.password = os.getenv("GMAIL_APP_PASSWORD")
        # Default recipient is the user themselves
        self.to_email = os.getenv("REPORT_RECIPIENT_EMAIL") or self.user

    def send(self, html_content: str, subject: str = "Weekly Intelligence Digest"):
        if not all([self.user, self.password]):
            console.print("[error]Gmail credentials missing. Set GMAIL_USER and GMAIL_APP_PASSWORD in .env.[/]")
            return False
            
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.user
        msg['To'] = self.to_email

        # Attach HTML content
        part = MIMEText(html_content, 'html')
        msg.attach(part)

        try:
            console.print(f"[info]Connecting to {self.server}...[/]")
            with smtplib.SMTP(self.server, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.user, self.to_email, msg.as_string())
            console.print(f"[success]Intelligence Digest delivered to {self.to_email}[/]")
            return True
        except Exception as e:
            console.print(f"[error]Failed to deliver digest: {e}[/]")
            return False

if __name__ == "__main__":
    pass
