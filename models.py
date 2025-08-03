from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class User(db.Model):
    """Model for storing user accounts with roles"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='viewer')  # 'admin' or 'viewer'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'
    
    def is_viewer(self):
        """Check if user has viewer role"""
        return self.role == 'viewer'
    
    def to_dict(self):
        """Convert User object to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class Product(db.Model):
    """Model for storing product information for email generation"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    url = db.Column(db.String(500), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert Product object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'image_url': self.image_url,
            'description': self.description,
            'price': self.price,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


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
    is_business = db.Column(db.Boolean, default=False)
    profile_pic_url = db.Column(db.String(500))
    is_duplicate = db.Column(db.Boolean, default=False)
    
    # Source post information from hashtag discovery
    source_timestamp = db.Column(db.DateTime)  # Post creation timestamp from hashtag search
    source_post_url = db.Column(db.String(500))  # Instagram post URL from hashtag search
    beitragstext = db.Column(db.Text)  # Post caption/content from hashtag search
    
    # Location/Address fields
    address_street = db.Column(db.String(300))
    city_name = db.Column(db.String(100))
    zip = db.Column(db.String(20))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Email outreach fields
    subject = db.Column(db.String(200))
    email_body = db.Column(db.Text)
    sent = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime)
    
    # Product selection for personalized emails
    selected_product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    selected_product = db.relationship('Product', backref='leads')
    
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
            'full_name': self.full_name,  # Add snake_case alias for compatibility
            'bio': self.bio,
            'email': self.email,
            'phone': self.phone,
            'website': self.website,
            'followersCount': self.followers_count,
            'followers_count': self.followers_count,  # Add snake_case alias for compatibility
            'followingCount': self.following_count,
            'postsCount': self.posts_count,
            'isVerified': self.is_verified,
            'isBusiness': self.is_business,
            'profilePicUrl': self.profile_pic_url,
            'is_duplicate': self.is_duplicate,
            'addressStreet': self.address_street,
            'cityName': self.city_name,
            'zip': self.zip,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'subject': self.subject,
            'emailBody': self.email_body,
            'email_body': self.email_body,  # Add snake_case alias for compatibility
            'sent': self.sent,
            'sentAt': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'selectedProductId': self.selected_product_id,
            'selectedProduct': self.selected_product.to_dict() if self.selected_product else None,
            'sourceTimestamp': self.source_timestamp.isoformat() if self.source_timestamp else None,
            'sourcePostUrl': self.source_post_url,
            'beitragstext': self.beitragstext
        }


class HashtagUsernamePair(db.Model):
    """Model for storing deduplicated hashtag-username pairs"""
    id = db.Column(db.Integer, primary_key=True)
    hashtag = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    is_duplicate = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime)  # Post creation timestamp
    post_url = db.Column(db.String(500))  # Instagram post URL
    beitragstext = db.Column(db.Text)  # Post caption/content
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
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'post_url': self.post_url,
            'beitragstext': self.beitragstext,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class LeadBackup(db.Model):
    """Backup model for Lead data - not affected by clear operations"""
    id = db.Column(db.Integer, primary_key=True)
    original_lead_id = db.Column(db.Integer, nullable=False)
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
    is_business = db.Column(db.Boolean, default=False)
    profile_pic_url = db.Column(db.String(500))
    is_duplicate = db.Column(db.Boolean, default=False)
    
    # Location/Address fields
    address_street = db.Column(db.String(300))
    city_name = db.Column(db.String(100))
    zip = db.Column(db.String(20))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Email outreach fields
    subject = db.Column(db.String(200))
    email_body = db.Column(db.Text)
    sent = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime)
    
    # Metadata
    original_created_at = db.Column(db.DateTime)
    original_updated_at = db.Column(db.DateTime)
    backup_created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert LeadBackup object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'original_lead_id': self.original_lead_id,
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
            'addressStreet': self.address_street,
            'cityName': self.city_name,
            'zip': self.zip,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'subject': self.subject,
            'emailBody': self.email_body,
            'sent': self.sent,
            'sentAt': self.sent_at.isoformat() if self.sent_at else None,
            'original_created_at': self.original_created_at.isoformat() if self.original_created_at else None,
            'backup_created_at': self.backup_created_at.isoformat() if self.backup_created_at else None
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


class SystemPrompt(db.Model):
    """Model for storing system prompts for email generation"""
    id = db.Column(db.Integer, primary_key=True)
    prompt_type = db.Column(db.String(20), nullable=False)  # 'subject' or 'body'
    has_product = db.Column(db.Boolean, nullable=False)  # True for with product, False for without
    system_message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert SystemPrompt object to dictionary"""
        return {
            'id': self.id,
            'prompt_type': self.prompt_type,
            'has_product': self.has_product,
            'system_message': self.system_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class UserPrompt(db.Model):
    """Model for storing user prompts/templates for email generation"""
    id = db.Column(db.Integer, primary_key=True)
    prompt_type = db.Column(db.String(20), nullable=False)  # 'subject' or 'body'
    has_product = db.Column(db.Boolean, nullable=False)  # True for with product, False for without
    user_message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert UserPrompt object to dictionary"""
        return {
            'id': self.id,
            'prompt_type': self.prompt_type,
            'has_product': self.has_product,
            'user_message': self.user_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class VariableSettings(db.Model):
    """Model for storing which variables are enabled for each prompt configuration"""
    id = db.Column(db.Integer, primary_key=True)
    prompt_type = db.Column(db.String(20), nullable=False)  # 'subject' or 'body'
    has_product = db.Column(db.Boolean, nullable=False)  # True for with product, False for without
    variable_name = db.Column(db.String(50), nullable=False)  # 'username', 'full_name', 'bio', etc.
    is_enabled = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite unique constraint to prevent duplicate configurations
    __table_args__ = (db.UniqueConstraint('prompt_type', 'has_product', 'variable_name', name='unique_variable_config'),)
    
    def to_dict(self):
        """Convert VariableSettings object to dictionary"""
        return {
            'id': self.id,
            'prompt_type': self.prompt_type,
            'has_product': self.has_product,
            'variable_name': self.variable_name,
            'is_enabled': self.is_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }