"""
AI Exam Manager — Notification Service
Centralized notification creation, dispatch, and retrieval.
"""
from models import db, Notification, User


def create_notification(user_id, title, message, category='info', severity='low', link=''):
    """Create a notification for a specific user and push via WebSocket."""
    notif = Notification(
        user_id=user_id, title=title, message=message,
        category=category, severity=severity, link=link
    )
    db.session.add(notif)
    db.session.commit()

    try:
        from realtime import emit_notification
        emit_notification(user_id, {
            'id': notif.id, 'title': title, 'message': message,
            'category': category, 'severity': severity, 'link': link,
            'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M')
        })
    except Exception:
        pass

    return notif


def broadcast_notification(title, message, category='info', severity='low', link=''):
    """Send a notification to all active users."""
    users = User.query.filter_by(is_active=True).all()
    for user in users:
        create_notification(user.id, title, message, category, severity, link)


def broadcast_role_notification(role, title, message, category='info', severity='low', link=''):
    """Send a notification to all users with a given role."""
    users = User.query.filter_by(role=role, is_active=True).all()
    for user in users:
        create_notification(user.id, title, message, category, severity, link)


def get_user_notifications(user_id, limit=50, unread_only=False):
    """Get notifications for a user, most recent first."""
    query = Notification.query.filter_by(user_id=user_id)
    if unread_only:
        query = query.filter_by(is_read=False)
    return query.order_by(Notification.created_at.desc()).limit(limit).all()


def get_unread_count(user_id):
    """Get count of unread notifications for a user."""
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()


def mark_read(notification_id, user_id):
    """Mark a single notification as read."""
    notif = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notif:
        notif.is_read = True
        db.session.commit()
    return notif


def mark_all_read(user_id):
    """Mark all notifications for a user as read."""
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
