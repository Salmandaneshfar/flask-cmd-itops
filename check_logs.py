#!/usr/bin/env python3
from app import create_app
from models import db, ActivityLog, User
from datetime import datetime

app = create_app()
with app.app_context():
    # Check total logs
    total_logs = ActivityLog.query.count()
    print(f"Total logs in database: {total_logs}")
    
    # Get recent logs
    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    print(f"\nRecent {len(recent_logs)} logs:")
    for log in recent_logs:
        print(f"ID: {log.id}, Action: {log.action}, User: {log.username}, Time: {log.created_at}")
    
    # Check if there are any users
    users = User.query.all()
    print(f"\nTotal users: {len(users)}")
    for user in users:
        print(f"User: {user.username}, Role: {user.role}, Active: {user.is_active}")