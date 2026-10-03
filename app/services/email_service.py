import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any

logger = logging.getLogger("uvicorn.error")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER or "noreply@dronevision.ai")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"


def send_email(to_email: str, subject: str, html_content: str, text_content: str = "") -> Dict[str, Any]:
    """
    Sends an email using configured SMTP settings.
    Gracefully logs email if SMTP credentials are not configured in the environment.
    """
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        logger.info(f"[EMAIL_DISPATCH_SIMULATED] To: {to_email} | Subject: {subject}")
        logger.info(f"[EMAIL_CONTENT] {text_content or html_content}")
        return {
            "sent": False,
            "simulated": True,
            "message": "SMTP not configured. Email logged to server diagnostics.",
            "to": to_email,
            "subject": subject,
        }

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM_EMAIL
        msg["To"] = to_email

        if text_content:
            msg.attach(MIMEText(text_content, "plain"))
        if html_content:
            msg.attach(MIMEText(html_content, "html"))

        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
            if SMTP_USE_TLS:
                server.starttls()

        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM_EMAIL, [to_email], msg.as_string())
        server.quit()

        logger.info(f"[EMAIL_DELIVERED] Sent successfully to {to_email}")
        return {"sent": True, "to": to_email}

    except Exception as e:
        logger.error(f"[EMAIL_DELIVERY_ERROR] Failed sending email to {to_email}: {e}")
        return {"sent": False, "error": str(e), "to": to_email}


def send_welcome_email(to_email: str, username: str) -> Dict[str, Any]:
    subject = "Welcome to DroneVision 3D / AutoDCR Portal"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">
      <h2 style="color: #0891b2;">Welcome to DroneVision, {username}!</h2>
      <p style="color: #475569; font-size: 14px; line-height: 1.6;">
        Your officer account has been successfully created. You can now ingest high-resolution aerial datasets,
        generate interactive 3D photogrammetry meshes, map geodesic flight paths, and perform municipal scrutiny.
      </p>
      <div style="margin: 20px 0; padding: 15px; background: #f8fafc; border-radius: 8px; border: 1px solid #cbd5e1;">
        <p style="margin: 0; font-size: 13px; color: #334155;"><b>Registered Account:</b> {to_email}</p>
        <p style="margin: 5px 0 0 0; font-size: 13px; color: #334155;"><b>Platform:</b> DroneVision 3D Photogrammetry & AutoDCR</p>
      </div>
      <p style="color: #94a3b8; font-size: 12px; margin-top: 30px;">
        This is an automated system notification from the DroneVision Enterprise Gateway.
      </p>
    </div>
    """
    text = f"Welcome to DroneVision, {username}! Your account ({to_email}) is ready to process drone survey datasets."
    return send_email(to_email, subject, html, text)


def send_password_reset_email(to_email: str, username: str, reset_token: str) -> Dict[str, Any]:
    subject = "DroneVision Password Reset Request"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">
      <h2 style="color: #0891b2;">Password Reset Request</h2>
      <p style="color: #475569; font-size: 14px; line-height: 1.6;">
        Hello {username}, we received a request to reset your password for your DroneVision officer account.
      </p>
      <div style="margin: 20px 0; padding: 15px; background: #f8fafc; border-radius: 8px; border: 1px solid #cbd5e1; text-align: center;">
        <p style="margin: 0 0 10px 0; font-size: 13px; color: #64748b;">Your Password Reset Token:</p>
        <span style="font-family: monospace; font-size: 16px; font-weight: bold; background: #e0f2fe; color: #0369a1; padding: 8px 16px; border-radius: 6px; display: inline-block;">
          {reset_token}
        </span>
      </div>
      <p style="color: #475569; font-size: 13px;">
        Enter this token on the password reset page along with your new password. This token will expire in 1 hour.
      </p>
      <p style="color: #94a3b8; font-size: 12px; margin-top: 30px;">
        If you did not request this password reset, please ignore this message.
      </p>
    </div>
    """
    text = f"Hello {username}, your password reset token is: {reset_token}. It expires in 1 hour."
    return send_email(to_email, subject, html, text)
