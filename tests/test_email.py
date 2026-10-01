from services.email_service import (
    MAIL_USERNAME,
    send_email,
)


send_email(
    recipient=MAIL_USERNAME,
    subject="ORSC CMS - Email Test",
    body=(
        "Hello,\n\n"
        "This is a test email sent automatically "
        "from the ORSC CMS.\n\n"
        "If you received this email, the email "
        "service is working correctly."
    ),
)


print("Email sent successfully!")