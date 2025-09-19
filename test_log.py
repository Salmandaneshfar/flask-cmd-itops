#!/usr/bin/env python3
from app import create_app
from models import db, ActivityLog
from flask import request

app = create_app()
with app.app_context():
    # Test creating a log entry manually
    try:
        log_entry = ActivityLog(
            user_id=1,
            username='test_user',
            action='test',
            model_name='test',
            record_id=1,
            method='POST',
            path='/test',
            status_code=200,
            details='Test log entry',
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        db.session.add(log_entry)
        db.session.commit()
        print("Test log entry created successfully!")
        
        # Check if it was saved
        logs = ActivityLog.query.all()
        print(f"Total logs now: {len(logs)}")
        for log in logs:
            print(f"Log: {log.action} by {log.username} at {log.created_at}")
            
    except Exception as e:
        print(f"Error creating log: {e}")
        db.session.rollback()
