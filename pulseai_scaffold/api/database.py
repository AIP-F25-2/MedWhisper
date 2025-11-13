# database.py
import duckdb
import os
import hashlib
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class UserDatabase:
    def __init__(self, db_path: str = "medwhisper_users.db"):
        """Initialize DuckDB connection and create tables if they don't exist."""
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._create_tables()
    
    def _create_tables(self):
        """Create user tables if they don't exist."""
        # Users table for basic login information
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email VARCHAR UNIQUE NOT NULL,
                password_hash VARCHAR NOT NULL,
                full_name VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # User profiles table for additional information
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                phone VARCHAR,
                date_of_birth DATE,
                gender VARCHAR,
                address TEXT,
                emergency_contact VARCHAR,
                medical_history TEXT,
                allergies TEXT,
                current_medications TEXT,
                insurance_provider VARCHAR,
                insurance_number VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        logger.info("Database tables created successfully")
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, email: str, password: str, full_name: str) -> Optional[int]:
        """Create a new user and return user ID."""
        try:
            password_hash = self.hash_password(password)
            
            # Check if user already exists
            existing_user = self.conn.execute(
                "SELECT id FROM users WHERE email = ?", [email]
            ).fetchone()
            
            if existing_user:
                logger.warning(f"User with email {email} already exists")
                return None
            
            # Insert new user
            # Get the next available ID
            max_id_result = self.conn.execute("SELECT COALESCE(MAX(id), 0) FROM users").fetchone()
            next_id = max_id_result[0] + 1
            
            self.conn.execute("""
                INSERT INTO users (id, email, password_hash, full_name)
                VALUES (?, ?, ?, ?)
            """, [next_id, email, password_hash, full_name])
            
            self.conn.commit()
            
            logger.info(f"User created successfully with ID: {next_id}")
            return next_id
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data if valid."""
        try:
            password_hash = self.hash_password(password)
            
            result = self.conn.execute("""
                SELECT id, email, full_name, created_at, is_active
                FROM users 
                WHERE email = ? AND password_hash = ? AND is_active = TRUE
            """, [email, password_hash])
            
            user = result.fetchone()
            
            if user:
                user_data = {
                    'id': user[0],
                    'email': user[1],
                    'full_name': user[2],
                    'created_at': user[3].isoformat() if user[3] else None,
                    'is_active': user[4]
                }
                logger.info(f"User {email} authenticated successfully")
                return user_data
            else:
                logger.warning(f"Authentication failed for email: {email}")
                return None
                
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    def update_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> bool:
        """Update user profile information."""
        try:
            # Check if profile exists
            existing_profile = self.conn.execute(
                "SELECT id FROM user_profiles WHERE user_id = ?", [user_id]
            ).fetchone()
            
            if existing_profile:
                # Update existing profile
                self.conn.execute("""
                    UPDATE user_profiles SET
                        phone = ?, date_of_birth = ?, gender = ?, address = ?,
                        emergency_contact = ?, medical_history = ?, allergies = ?,
                        current_medications = ?, insurance_provider = ?,
                        insurance_number = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, [
                    profile_data.get('phone'),
                    profile_data.get('date_of_birth'),
                    profile_data.get('gender'),
                    profile_data.get('address'),
                    profile_data.get('emergency_contact'),
                    profile_data.get('medical_history'),
                    profile_data.get('allergies'),
                    profile_data.get('current_medications'),
                    profile_data.get('insurance_provider'),
                    profile_data.get('insurance_number'),
                    user_id
                ])
            else:
                # Create new profile
                # Get the next available ID
                max_id_result = self.conn.execute("SELECT COALESCE(MAX(id), 0) FROM user_profiles").fetchone()
                next_id = max_id_result[0] + 1
                
                self.conn.execute("""
                    INSERT INTO user_profiles (
                        id, user_id, phone, date_of_birth, gender, address,
                        emergency_contact, medical_history, allergies,
                        current_medications, insurance_provider, insurance_number
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    next_id, user_id,
                    profile_data.get('phone'),
                    profile_data.get('date_of_birth'),
                    profile_data.get('gender'),
                    profile_data.get('address'),
                    profile_data.get('emergency_contact'),
                    profile_data.get('medical_history'),
                    profile_data.get('allergies'),
                    profile_data.get('current_medications'),
                    profile_data.get('insurance_provider'),
                    profile_data.get('insurance_number')
                ])
            
            self.conn.commit()
            logger.info(f"User profile updated for user ID: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile information."""
        try:
            result = self.conn.execute("""
                SELECT u.id, u.email, u.full_name, u.created_at,
                       p.phone, p.date_of_birth, p.gender, p.address,
                       p.emergency_contact, p.medical_history, p.allergies,
                       p.current_medications, p.insurance_provider, p.insurance_number
                FROM users u
                LEFT JOIN user_profiles p ON u.id = p.user_id
                WHERE u.id = ? AND u.is_active = TRUE
            """, [user_id])
            
            user = result.fetchone()
            
            if user:
                return {
                    'id': user[0],
                    'email': user[1],
                    'full_name': user[2],
                    'created_at': user[3],
                    'phone': user[4],
                    'date_of_birth': user[5],
                    'gender': user[6],
                    'address': user[7],
                    'emergency_contact': user[8],
                    'medical_history': user[9],
                    'allergies': user[10],
                    'current_medications': user[11],
                    'insurance_provider': user[12],
                    'insurance_number': user[13]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def close(self):
        """Close database connection."""
        self.conn.close()

# Global database instance
db = UserDatabase()
