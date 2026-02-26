from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from config import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Detect missing or placeholder SendGrid API key
        api_key = settings.SENDGRID_API_KEY
        if not api_key or api_key == "SG.placeholder" or not api_key.startswith("SG."):
            logger.warning('SendGrid API key not configured or invalid. EmailService running in DEMO mode.')
            self.demo_mode = True
            self.sg = None
        else:
            self.demo_mode = False
            self.sg = SendGridAPIClient(api_key)
        self.from_email = settings.SENDGRID_FROM_EMAIL
        self.from_name = settings.SENDGRID_FROM_NAME

    def send_otp_email(self, to_email: str, otp_code: str, purpose: str):
        # Development Fallback: Log the OTP so it can be retrieved from logs if email fails or in dev
        logger.warning(f"--- OTP DEBUG LOG ---")
        logger.warning(f"Recipient: {to_email}")
        logger.warning(f"Purpose: {purpose}")
        logger.warning(f"OTP Code: {otp_code}")
        logger.warning(f"---------------------")

        subject = "Your Veritas AI Verification Code"
        if purpose == "password_reset":
            subject = "Veritas AI - Password Reset Request"
        
        content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <h2 style="color: #646cff; text-align: center;">Veritas AI</h2>
            <p>Hello,</p>
            <p>You requested a verification code for <strong>{purpose.replace('_', ' ')}</strong>.</p>
            <div style="background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                {otp_code}
            </div>
            <p>This code will expire in 10 minutes. If you did not request this, please ignore this email.</p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #888; text-align: center;">&copy; 2026 Veritas AI. All rights reserved.</p>
        </div>
        """
        
        message = Mail(
            from_email=(self.from_email, self.from_name),
            to_emails=to_email,
            subject=subject,
            html_content=content
        )
        
        if self.demo_mode:
            logger.warning(f"DEMO MODE: Skipping actual email send to {to_email}. OTP is logged above.")
            return True

        try:
            response = self.sg.send(message)
            if response.status_code == 202:
                logger.warning(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.warning(f"SendGrid error status: {response.status_code}")
                # ... existing logging ...
                return False
        except Exception as e:
            logger.error(f"Detailed SendGrid Exception: {str(e)}")
            return False

    def send_welcome_email(self, to_email: str, password: str, role: str):
        """Send a welcome email to a new user created by an admin."""
        # Development Fallback: Log the credentials so they can be retrieved from logs
        logger.warning(f"--- WELCOME EMAIL DEBUG LOG ---")
        logger.warning(f"Recipient: {to_email}")
        logger.warning(f"Role: {role}")
        logger.warning(f"Password: {password}")
        logger.warning(f"-------------------------------")

        subject = "Welcome to Veritas AI - Your Account Credentials"
        
        content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <h2 style="color: #646cff; text-align: center;">Welcome to Veritas AI</h2>
            <p>Hello,</p>
            <p>An administrator has created an account for you on Veritas AI.</p>
            <div style="background-color: #f4f4f4; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Email:</strong> {to_email}</p>
                <p style="margin: 5px 0;"><strong>Password:</strong> {password}</p>
                <p style="margin: 5px 0;"><strong>Role:</strong> {role.replace('_', ' ').capitalize()}</p>
            </div>
            <p>Please log in at your earliest convenience and change your password for security.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="http://localhost:5173/login" style="background-color: #646cff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Login to Dashboard</a>
            </div>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #888; text-align: center;">&copy; 2026 Veritas AI. All rights reserved.</p>
        </div>
        """
        
        message = Mail(
            from_email=(self.from_email, self.from_name),
            to_emails=to_email,
            subject=subject,
            html_content=content
        )
        
        try:
            response = self.sg.send(message)
            if response.status_code == 202:
                logger.warning(f"Welcome email sent successfully to {to_email}")
                return True
            else:
                logger.warning(f"SendGrid welcome email error status: {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Detailed SendGrid Welcome Email Exception: {str(e)}")
            return False

email_service = EmailService()
