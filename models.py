from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Lead(db.Model):
    """Model for storing Instagram lead data"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    hashtag = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(200))
    bio = db.Column(db.Text)
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    website = db.Column(db.String(200))
    followers_count = db.Column(db.Integer, default=0)
    following_count = db.Column(db.Integer, default=0)
    posts_count = db.Column(db.Integer, default=0)
    is_verified = db.Column(db.Boolean, default=False)
    profile_pic_url = db.Column(db.String(500))
    is_duplicate = db.Column(db.Boolean, default=False)
    
    # Email outreach fields
    subject = db.Column(db.String(200))
    email_body = db.Column(db.Text)
    sent = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite unique constraint to prevent duplicates
    __table_args__ = (db.UniqueConstraint('username', 'hashtag', name='unique_username_hashtag'),)
    
    def to_dict(self):
        """Convert Lead object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'username': self.username,
            'hashtag': self.hashtag,
            'fullName': self.full_name,
            'bio': self.bio,
            'email': self.email,
            'phone': self.phone,
            'website': self.website,
            'followersCount': self.followers_count,
            'followingCount': self.following_count,
            'postsCount': self.posts_count,
            'isVerified': self.is_verified,
            'profilePicUrl': self.profile_pic_url,
            'is_duplicate': self.is_duplicate,
            'subject': self.subject,
            'emailBody': self.email_body,
            'sent': self.sent,
            'sentAt': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class HashtagUsernamePair(db.Model):
    """Model for storing deduplicated hashtag-username pairs"""
    id = db.Column(db.Integer, primary_key=True)
    hashtag = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    is_duplicate = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite unique constraint to prevent duplicates
    __table_args__ = (db.UniqueConstraint('hashtag', 'username', name='unique_hashtag_username_pair'),)
    
    def to_dict(self):
        """Convert HashtagUsernamePair object to dictionary"""
        return {
            'id': self.id,
            'hashtag': self.hashtag,
            'username': self.username,
            'is_duplicate': self.is_duplicate,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ProcessingSession(db.Model):
    """Model for tracking processing sessions"""
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), nullable=False)
    search_limit = db.Column(db.Integer, default=100)
    status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    leads_found = db.Column(db.Integer, default=0)
    ig_sessionid_hash = db.Column(db.String(100))  # Store hash for privacy
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    
    def to_dict(self):
        """Convert ProcessingSession object to dictionary"""
        return {
            'id': self.id,
            'keyword': self.keyword,
            'search_limit': self.search_limit,
            'status': self.status,
            'leads_found': self.leads_found,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }