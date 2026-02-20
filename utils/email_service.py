"""Email service for sending notifications"""

import logging
import threading
from flask import current_app, render_template
from flask_mail import Message
from app import mail

logger = logging.getLogger(__name__)


def is_mail_configured():
    """Check if email service is properly configured.
    
    Returns:
        bool: True if mail server and credentials are configured
    """
    app = current_app._get_current_object()
    mail_server = app.config.get('MAIL_SERVER')
    mail_username = app.config.get('MAIL_USERNAME')
    
    # Check if essential mail settings are present
    return bool(mail_server and mail_username)


def send_async_email(app, msg):
    """Send email asynchronously in a separate thread"""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send email: {e}")


def send_email(subject, recipient, template_html, template_txt, **kwargs):
    """Send email with both HTML and plain text versions

    Args:
        subject: Email subject line
        recipient: Recipient email address
        template_html: Path to HTML template
        template_txt: Path to plain text template
        **kwargs: Template variables
        
    Returns:
        Thread object if email was sent, None if mail not configured
    """
    # Skip if mail service is not configured
    if not is_mail_configured():
        logger.info(f"Mail not configured - skipping email to {recipient}: {subject}")
        return None
    
    app = current_app._get_current_object()

    # Create message
    msg = Message(
        subject=subject,
        recipients=[recipient],
        sender=app.config.get('MAIL_DEFAULT_SENDER')
    )

    # Render templates
    msg.html = render_template(template_html, **kwargs)
    msg.body = render_template(template_txt, **kwargs)

    # Send asynchronously
    thread = threading.Thread(target=send_async_email, args=(app, msg))
    thread.start()

    return thread


def send_discussion_notification(trip, message, author, recipients):
    """Send notification to trip participants about new discussion message

    Args:
        trip: Trip object
        message: TripDiscussion message object
        author: User who posted the message
        recipients: List of user objects to notify (excluding author)
    """
    app = current_app._get_current_object()

    # Don't send if no recipients
    if not recipients:
        return

    subject = f"Novo sporočilo za izlet: {trip.title}"

    # Send individual emails to each recipient
    threads = []
    for recipient_user in recipients:
        if recipient_user.email:
            thread = send_email(
                subject=subject,
                recipient=recipient_user.email,
                template_html='emails/discussion_notification.html',
                template_txt='emails/discussion_notification.txt',
                trip=trip,
                message=message,
                author=author,
                recipient_user=recipient_user
            )
            if thread:  # Only append if email was actually sent
                threads.append(thread)

    return threads


def get_discussion_notification_recipients(trip, exclude_user_id):
    """Get list of users who should receive discussion notifications

    Args:
        trip: Trip object
        exclude_user_id: User ID to exclude (typically the message author)

    Returns:
        List of User objects who have notification enabled and are confirmed participants
    """
    from models.trip import ParticipantStatus

    recipients = []

    from models.user import NotificationType

    for participant in trip.participants:
        # Only notify confirmed participants who have notifications enabled
        # Check both per-trip setting and global user preference
        if (participant.status == ParticipantStatus.CONFIRMED and
            participant.notify_discussion and
            participant.user_id != exclude_user_id and
            participant.user.get_notification_preference(NotificationType.DISCUSSIONS)):
            recipients.append(participant.user)

    return recipients
