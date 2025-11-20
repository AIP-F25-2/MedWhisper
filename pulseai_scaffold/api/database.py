# database.py
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import hashlib
from typing import Optional, Dict, Any
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class UserDatabase:
    def __init__(self):
        """Initialize PostgreSQL connection and create tables if they don't exist."""
        # Get database connection parameters from environment variables
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5433'),  # Default to PostgreSQL 18
            'database': os.getenv('POSTGRES_DB', 'medwhisper'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'root')  # Default password
        }
        self._create_tables()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _create_tables(self):
        """Create user tables if they don't exist."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Users table for basic login information
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        full_name VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
                
                # User profiles table for additional information
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        phone VARCHAR(50),
                        date_of_birth DATE,
                        gender VARCHAR(20),
                        address TEXT,
                        emergency_contact VARCHAR(255),
                        medical_history TEXT,
                        allergies TEXT,
                        current_medications TEXT,
                        insurance_provider VARCHAR(255),
                        insurance_number VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """)
                
                # Doctors table - healthcare providers
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS doctors (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER,
                        name VARCHAR(255) NOT NULL,
                        specialization VARCHAR(255),
                        license_number VARCHAR(100),
                        phone VARCHAR(50),
                        email VARCHAR(255),
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                    )
                """)
                
                # Patients table - links users to patient records
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS patients (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER,
                        patient_id VARCHAR(50) UNIQUE,
                        first_name VARCHAR(255) NOT NULL,
                        last_name VARCHAR(255) NOT NULL,
                        date_of_birth DATE,
                        gender VARCHAR(20),
                        phone VARCHAR(50),
                        email VARCHAR(255),
                        address TEXT,
                        emergency_contact_name VARCHAR(255),
                        emergency_contact_phone VARCHAR(50),
                        insurance_provider VARCHAR(255),
                        insurance_number VARCHAR(255),
                        status VARCHAR(50) DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                    )
                """)
                
                # Appointments table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS appointments (
                        id SERIAL PRIMARY KEY,
                        patient_id INTEGER NOT NULL,
                        doctor_id INTEGER,
                        appointment_date TIMESTAMP NOT NULL,
                        duration_minutes INTEGER DEFAULT 30,
                        status VARCHAR(50) DEFAULT 'scheduled',
                        reason TEXT,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE SET NULL
                    )
                """)
                
                # Medical records table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS medical_records (
                        id SERIAL PRIMARY KEY,
                        patient_id INTEGER NOT NULL,
                        doctor_id INTEGER,
                        record_type VARCHAR(100),
                        diagnosis TEXT,
                        treatment TEXT,
                        medications TEXT,
                        notes TEXT,
                        record_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE SET NULL
                    )
                """)
                
                # Vitals table - patient vital signs
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vitals (
                        id SERIAL PRIMARY KEY,
                        patient_id INTEGER NOT NULL,
                        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        temperature DECIMAL(5,2),
                        blood_pressure_systolic INTEGER,
                        blood_pressure_diastolic INTEGER,
                        heart_rate INTEGER,
                        respiratory_rate INTEGER,
                        oxygen_saturation DECIMAL(5,2),
                        weight DECIMAL(5,2),
                        height DECIMAL(5,2),
                        notes TEXT,
                        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
                    )
                """)
                
                # Chatbot logs table - store chatbot conversations
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chatbot_logs (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER,
                        patient_id INTEGER,
                        sender VARCHAR(255),
                        message TEXT NOT NULL,
                        response TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE SET NULL
                    )
                """)
                
                # Tasks table - for dashboard tasks
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER,
                        patient_id INTEGER,
                        title VARCHAR(255) NOT NULL,
                        description TEXT,
                        status VARCHAR(50) DEFAULT 'pending',
                        priority VARCHAR(50) DEFAULT 'medium',
                        due_date TIMESTAMP,
                        completed_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE SET NULL
                    )
                """)
                
                # Alerts table - for dashboard alerts
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id SERIAL PRIMARY KEY,
                        patient_id INTEGER,
                        alert_type VARCHAR(100),
                        message TEXT NOT NULL,
                        severity VARCHAR(50) DEFAULT 'medium',
                        is_read BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
                    )
                """)
                
                conn.commit()
                logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, email: str, password: str, full_name: str) -> Optional[int]:
        """Create a new user and return user ID."""
        try:
            password_hash = self.hash_password(password)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user already exists
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    logger.warning(f"User with email {email} already exists")
                    return None
                
                # Insert new user (PostgreSQL SERIAL will auto-generate ID)
                cursor.execute("""
                    INSERT INTO users (email, password_hash, full_name)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (email, password_hash, full_name))
                
                user_id = cursor.fetchone()[0]
                logger.info(f"User created successfully with ID: {user_id}")
                return user_id
            
        except psycopg2.IntegrityError as e:
            logger.warning(f"User with email {email} already exists: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data if valid."""
        try:
            password_hash = self.hash_password(password)
            
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                cursor.execute("""
                    SELECT id, email, full_name, created_at, is_active
                    FROM users 
                    WHERE email = %s AND password_hash = %s AND is_active = TRUE
                """, (email, password_hash))
                
                user = cursor.fetchone()
                
                if user:
                    user_data = {
                        'id': user['id'],
                        'email': user['email'],
                        'full_name': user['full_name'],
                        'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                        'is_active': user['is_active']
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
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if profile exists
                cursor.execute("SELECT id FROM user_profiles WHERE user_id = %s", (user_id,))
                existing_profile = cursor.fetchone()
                
                if existing_profile:
                    # Update existing profile
                    cursor.execute("""
                        UPDATE user_profiles SET
                            phone = %s, date_of_birth = %s, gender = %s, address = %s,
                            emergency_contact = %s, medical_history = %s, allergies = %s,
                            current_medications = %s, insurance_provider = %s,
                            insurance_number = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                    """, (
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
                    ))
                else:
                    # Create new profile (PostgreSQL SERIAL will auto-generate ID)
                    cursor.execute("""
                        INSERT INTO user_profiles (
                            user_id, phone, date_of_birth, gender, address,
                            emergency_contact, medical_history, allergies,
                            current_medications, insurance_provider, insurance_number
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        user_id,
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
                    ))
                
                logger.info(f"User profile updated for user ID: {user_id}")
                return True
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile information."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                cursor.execute("""
                    SELECT u.id, u.email, u.full_name, u.created_at,
                           p.phone, p.date_of_birth, p.gender, p.address,
                           p.emergency_contact, p.medical_history, p.allergies,
                           p.current_medications, p.insurance_provider, p.insurance_number
                    FROM users u
                    LEFT JOIN user_profiles p ON u.id = p.user_id
                    WHERE u.id = %s AND u.is_active = TRUE
                """, (user_id,))
                
                user = cursor.fetchone()
                
                if user:
                    return {
                        'id': user['id'],
                        'email': user['email'],
                        'full_name': user['full_name'],
                        'created_at': user['created_at'],
                        'phone': user['phone'],
                        'date_of_birth': user['date_of_birth'],
                        'gender': user['gender'],
                        'address': user['address'],
                        'emergency_contact': user['emergency_contact'],
                        'medical_history': user['medical_history'],
                        'allergies': user['allergies'],
                        'current_medications': user['current_medications'],
                        'insurance_provider': user['insurance_provider'],
                        'insurance_number': user['insurance_number']
                    }
                return None
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    # ========== PATIENT METHODS ==========
    
    def get_all_patients(self, limit: int = 100, offset: int = 0) -> list:
        """Get all patients with pagination."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    SELECT p.*, u.email as user_email
                    FROM patients p
                    LEFT JOIN users u ON p.user_id = u.id
                    WHERE p.status = 'active'
                    ORDER BY p.created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting patients: {e}")
            return []
    
    def get_patient_count(self) -> int:
        """Get total count of active patients."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM patients WHERE status = 'active'")
                return cursor.fetchone()[0] or 0
        except Exception as e:
            logger.error(f"Error getting patient count: {e}")
            return 0
    
    def get_patient_by_id(self, patient_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific patient by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    SELECT p.*, u.email as user_email
                    FROM patients p
                    LEFT JOIN users u ON p.user_id = u.id
                    WHERE p.id = %s
                """, (patient_id,))
                patient = cursor.fetchone()
                return dict(patient) if patient else None
        except Exception as e:
            logger.error(f"Error getting patient: {e}")
            return None
    
    def create_patient(self, patient_data: Dict[str, Any]) -> Optional[int]:
        """Create a new patient record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO patients (
                        user_id, patient_id, first_name, last_name, date_of_birth,
                        gender, phone, email, address, emergency_contact_name,
                        emergency_contact_phone, insurance_provider, insurance_number, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    patient_data.get('user_id'),
                    patient_data.get('patient_id'),
                    patient_data.get('first_name'),
                    patient_data.get('last_name'),
                    patient_data.get('date_of_birth'),
                    patient_data.get('gender'),
                    patient_data.get('phone'),
                    patient_data.get('email'),
                    patient_data.get('address'),
                    patient_data.get('emergency_contact_name'),
                    patient_data.get('emergency_contact_phone'),
                    patient_data.get('insurance_provider'),
                    patient_data.get('insurance_number'),
                    patient_data.get('status', 'active')
                ))
                patient_id = cursor.fetchone()[0]
                logger.info(f"Patient created with ID: {patient_id}")
                return patient_id
        except Exception as e:
            logger.error(f"Error creating patient: {e}")
            return None
    
    # ========== APPOINTMENT METHODS ==========
    
    def get_today_appointments_count(self) -> int:
        """Get count of appointments scheduled for today."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM appointments
                    WHERE DATE(appointment_date) = CURRENT_DATE
                    AND status IN ('scheduled', 'confirmed')
                """)
                return cursor.fetchone()[0] or 0
        except Exception as e:
            logger.error(f"Error getting today's appointments count: {e}")
            return 0
    
    def get_appointments(self, limit: int = 50, patient_id: Optional[int] = None) -> list:
        """Get appointments with optional patient filter."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                if patient_id:
                    cursor.execute("""
                        SELECT a.*, p.first_name, p.last_name, d.name as doctor_name
                        FROM appointments a
                        LEFT JOIN patients p ON a.patient_id = p.id
                        LEFT JOIN doctors d ON a.doctor_id = d.id
                        WHERE a.patient_id = %s
                        ORDER BY a.appointment_date DESC
                        LIMIT %s
                    """, (patient_id, limit))
                else:
                    cursor.execute("""
                        SELECT a.*, p.first_name, p.last_name, d.name as doctor_name
                        FROM appointments a
                        LEFT JOIN patients p ON a.patient_id = p.id
                        LEFT JOIN doctors d ON a.doctor_id = d.id
                        ORDER BY a.appointment_date DESC
                        LIMIT %s
                    """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting appointments: {e}")
            return []
    
    # ========== ALERTS METHODS ==========
    
    def get_unread_alerts_count(self) -> int:
        """Get count of unread alerts."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM alerts WHERE is_read = FALSE")
                return cursor.fetchone()[0] or 0
        except Exception as e:
            logger.error(f"Error getting alerts count: {e}")
            return 0
    
    # ========== QUEUE METHODS ==========
    
    def get_queue_count(self) -> int:
        """Get count of patients in queue (pending appointments)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM appointments
                    WHERE status = 'pending' OR status = 'waiting'
                """)
                return cursor.fetchone()[0] or 0
        except Exception as e:
            logger.error(f"Error getting queue count: {e}")
            return 0
    
    # ========== VITALS METHODS ==========
    
    def get_patient_vitals(self, patient_id: int, limit: int = 10) -> list:
        """Get recent vital signs for a patient."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    SELECT * FROM vitals
                    WHERE patient_id = %s
                    ORDER BY recorded_at DESC
                    LIMIT %s
                """, (patient_id, limit))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting vitals: {e}")
            return []
    
    # ========== TASKS METHODS ==========
    
    def get_tasks(self, user_id: Optional[int] = None, status: Optional[str] = None) -> list:
        """Get tasks, optionally filtered by user and status."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                query = "SELECT * FROM tasks WHERE 1=1"
                params = []
                
                if user_id:
                    query += " AND user_id = %s"
                    params.append(user_id)
                
                if status:
                    query += " AND status = %s"
                    params.append(status)
                
                query += " ORDER BY created_at DESC LIMIT 20"
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return []
    
    # ========== DASHBOARD STATISTICS ==========
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get all dashboard statistics in one call."""
        try:
            return {
                'active_patients': self.get_patient_count(),
                'today_appointments': self.get_today_appointments_count(),
                'alerts': self.get_unread_alerts_count(),
                'queue': self.get_queue_count()
            }
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {
                'active_patients': 0,
                'today_appointments': 0,
                'alerts': 0,
                'queue': 0
            }

# Global database instance
db = UserDatabase()
