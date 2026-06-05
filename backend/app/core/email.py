import logging
from email.message import EmailMessage

from aiosmtplib import send

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email(email_to: str, subject: str, html_content: str) -> None:
    """Send an email using SMTP if configured."""
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP configuration is missing. Printing email to console instead.")
        logger.warning(f"--- EMAIL TO: {email_to} ---")
        logger.warning(f"--- SUBJECT: {subject} ---")
        logger.warning(f"--- CONTENT: {html_content} ---")
        return

    assert settings.EMAILS_FROM_EMAIL, "EMAILS_FROM_EMAIL must be set"

    message = EmailMessage()
    message["From"] = settings.EMAILS_FROM_EMAIL
    message["To"] = email_to
    message["Subject"] = subject
    message.add_alternative(html_content, subtype="html")

    try:
        await send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.SMTP_TLS,
        )
        logger.info(f"Successfully sent email to {email_to}")
    except Exception as e:
        logger.error(f"Failed to send email to {email_to}: {e}")


async def send_reset_password_email(email_to: str, token: str) -> None:
    """Send a password reset email."""
    project_name = settings.APP_NAME
    subject = f"{project_name} - Password Reset"
    link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    btn_style = (
        "display: inline-block; padding: 10px 20px; background-color: #000; "
        "color: #fff; text-decoration: none; font-weight: bold; border-radius: 4px;"
    )

    html_content = f"""
    <html>
      <body style="font-family: sans-serif; line-height: 1.5; color: #333;">
        <h2>Password Reset</h2>
        <p>You recently requested to reset your password for your {project_name} account.</p>
        <p>Click the link below to reset it. This link will expire in 24 hours.</p>
        <p>
          <a href="{link}" style="{btn_style}">
            Reset Password
          </a>
        </p>
        <p>If you did not request a password reset, please ignore this email or
        contact support if you have concerns.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;" />
        <p style="font-size: 12px; color: #999;">
          If the button above does not work, copy and paste this link into your browser:<br/>
          {link}
        </p>
      </body>
    </html>
    """

    await send_email(email_to, subject, html_content)
