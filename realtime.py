"""
AI Exam Manager — Real-time WebSocket Event System
Flask-SocketIO initialization and notification dispatch helpers.
"""
from flask_socketio import SocketIO, emit, join_room
from flask_login import current_user

socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')


def init_realtime(app):
    """Initialize SocketIO with the Flask app and register event handlers."""
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')

    @socketio.on('connect')
    def on_connect():
        if current_user.is_authenticated:
            join_room(f'user_{current_user.id}')
            join_room(f'role_{current_user.role}')
            join_room('all_users')

    @socketio.on('disconnect')
    def on_disconnect():
        pass


def emit_notification(user_id, notification_dict):
    """Push a notification to a specific user's room."""
    socketio.emit('notification', notification_dict, room=f'user_{user_id}')


def emit_broadcast(notification_dict):
    """Push a notification to all connected users."""
    socketio.emit('notification', notification_dict, room='all_users')


def emit_role_notification(role, notification_dict):
    """Push a notification to all users with a given role."""
    socketio.emit('notification', notification_dict, room=f'role_{role}')


def emit_conflict_alert(conflict_dict):
    """Push a conflict alert to all admin users."""
    socketio.emit('conflict_alert', conflict_dict, room='role_admin')
