"""Email service for sending transactional emails."""

import logging
import os
from typing import Optional

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Brevo (formerly Sendinblue)."""
    
    def __init__(self):
        """Initialize email service with Brevo API key."""
        self.api_key = os.getenv("BREVO_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@frankenagent.dev")
        self.from_name = os.getenv("FROM_NAME", "FrankenAgent Lab")
        
        if not self.api_key:
            logger.warning("BREVO_API_KEY not set - emails will be logged only")
            self.client = None
        else:
            # Configure Brevo API client
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = self.api_key
            self.client = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
            )
    
    async def send_password_reset_email(
        self,
        to_email: str,
        reset_url: str,
        user_name: Optional[str] = None
    ) -> bool:
        """
        Send password reset email.
        
        Args:
            to_email: Recipient email address
            reset_url: Password reset URL with token
            user_name: Optional user's name for personalization
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = "Reset Your FrankenAgent Password"
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧪 FrankenAgent Lab</h1>
                </div>
                <div class="content">
                    <h2>Reset Your Password</h2>
                    <p>Hello{f" {user_name}" if user_name else ""},</p>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #667eea;">{reset_url}</p>
                    <p><strong>This link will expire in 1 hour.</strong></p>
                    <p>If you didn't request a password reset, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2025 FrankenAgent Lab. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text fallback
        text_content = f"""
        Reset Your Password
        
        Hello{f" {user_name}" if user_name else ""},
        
        We received a request to reset your password. Click the link below to create a new password:
        
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, you can safely ignore this email.
        
        © 2025 FrankenAgent Lab
        """
        
        return await self._send_email(to_email, subject, html_content, text_content)
    
    async def send_password_changed_email(
        self,
        to_email: str,
        user_name: Optional[str] = None
    ) -> bool:
        """
        Send password changed confirmation email.
        
        Args:
            to_email: Recipient email address
            user_name: Optional user's name for personalization
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = "Your FrankenAgent Password Was Changed"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧪 FrankenAgent Lab</h1>
                </div>
                <div class="content">
                    <h2>Password Changed Successfully</h2>
                    <p>Hello{f" {user_name}" if user_name else ""},</p>
                    <p>This is a confirmation that your password was successfully changed.</p>
                    <p>If you didn't make this change, please contact support immediately.</p>
                </div>
                <div class="footer">
                    <p>© 2025 FrankenAgent Lab. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Changed Successfully
        
        Hello{f" {user_name}" if user_name else ""},
        
        This is a confirmation that your password was successfully changed.
        
        If you didn't make this change, please contact support immediately.
        
        © 2025 FrankenAgent Lab
        """
        
        return await self._send_email(to_email, subject, html_content, text_content)
    
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str
    ) -> bool:
        """
        Internal method to send email via Brevo.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.client:
            # Log email instead of sending (for development)
            logger.info(f"[EMAIL] To: {to_email}")
            logger.info(f"[EMAIL] Subject: {subject}")
            logger.info(f"[EMAIL] Content:\n{text_content}")
            return True
        
        try:
            # Create email message for Brevo
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": to_email}],
                sender={"name": self.from_name, "email": self.from_email},
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            # Send email via Brevo API
            response = self.client.send_transac_email(send_smtp_email)
            
            logger.info(f"Email sent successfully to {to_email} (Message ID: {response.message_id})")
            return True
        
        except ApiException as e:
            logger.error(f"Brevo API error sending email to {to_email}: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}", exc_info=True)
            return False
