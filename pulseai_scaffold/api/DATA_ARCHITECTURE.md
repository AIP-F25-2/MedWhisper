# MedWhisper Data Architecture Documentation

This document explains how data, patients, doctors, features, and dashboard information are stored in the MedWhisper project.

## Overview

MedWhisper uses **PostgreSQL 18** as its primary database. The database stores all user authentication, patient records, medical data, appointments, and dashboard information.

## Database Connection

- **Host**: `localhost` (configurable via `POSTGRES_HOST` env variable)
- **Port**: `5433` (PostgreSQL 18 default, configurable via `POSTGRES_PORT`)
- **Database**: `medwhisper` (configurable via `POSTGRES_DB`)
- **User**: `postgres` (configurable via `POSTGRES_USER`)
- **Password**: `root` (configurable via `POSTGRES_PASSWORD`)

Configuration is stored in `.env` file in `pulseai_scaffold/api/` directory.

## Database Schema

### 1. **Users Table** (`users`)
Stores basic user authentication information.

**Columns:**
- `id` (SERIAL PRIMARY KEY) - Auto-incrementing user ID
- `email` (VARCHAR(255) UNIQUE) - User email (unique)
- `password_hash` (VARCHAR(255)) - SHA-256 hashed password
- `full_name` (VARCHAR(255)) - User's full name
- `created_at` (TIMESTAMP) - Account creation timestamp
- `is_active` (BOOLEAN) - Whether account is active (default: TRUE)

**Purpose**: Handles login/signup authentication. Each user must have a unique email.

---

### 2. **User Profiles Table** (`user_profiles`)
Stores additional user profile information (linked to users).

**Columns:**
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER) - Foreign key to `users.id`
- `phone` (VARCHAR(50)) - Phone number
- `date_of_birth` (DATE) - Date of birth
- `gender` (VARCHAR(20)) - Gender
- `address` (TEXT) - Physical address
- `emergency_contact` (VARCHAR(255)) - Emergency contact info
- `medical_history` (TEXT) - Medical history notes
- `allergies` (TEXT) - Known allergies
- `current_medications` (TEXT) - Current medications
- `insurance_provider` (VARCHAR(255)) - Insurance company
- `insurance_number` (VARCHAR(255)) - Insurance policy number
- `created_at` (TIMESTAMP) - Profile creation time
- `updated_at` (TIMESTAMP) - Last update time

**Purpose**: Stores extended user information collected during signup/profile updates.

**Relationship**: One-to-one with `users` table (one user can have one profile).

---

### 3. **Doctors Table** (`doctors`)
Stores healthcare provider/doctor information.

**Columns:**
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER) - Optional foreign key to `users.id` (if doctor is also a user)
- `name` (VARCHAR(255)) - Doctor's full name
- `specialization` (VARCHAR(255)) - Medical specialization
- `license_number` (VARCHAR(100)) - Medical license number
- `phone` (VARCHAR(50)) - Contact phone
- `email` (VARCHAR(255)) - Contact email
- `is_active` (BOOLEAN) - Whether doctor is active (default: TRUE)
- `created_at` (TIMESTAMP) - Record creation time

**Purpose**: Manages healthcare provider information. Doctors can be linked to user accounts or exist independently.

---

### 4. **Patients Table** (`patients`)
Stores patient records and medical information.

**Columns:**
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER) - Optional foreign key to `users.id` (if patient is also a user)
- `patient_id` (VARCHAR(50) UNIQUE) - Unique patient identifier
- `first_name` (VARCHAR(255)) - Patient's first name
- `last_name` (VARCHAR(255)) - Patient's last name
- `date_of_birth` (DATE) - Date of birth
- `gender` (VARCHAR(20)) - Gender
- `phone` (VARCHAR(50)) - Contact phone
- `email` (VARCHAR(255)) - Contact email
- `address` (TEXT) - Physical address
- `emergency_contact_name` (VARCHAR(255)) - Emergency contact name
- `emergency_contact_phone` (VARCHAR(50)) - Emergency contact phone
- `insurance_provider` (VARCHAR(255)) - Insurance company
- `insurance_number` (VARCHAR(255)) - Insurance policy number
- `status` (VARCHAR(50)) - Patient status (default: 'active')
- `created_at` (TIMESTAMP) - Record creation time
- `updated_at` (TIMESTAMP) - Last update time

**Purpose**: Central table for all patient information. This is the main table used in the dashboard to display patient data.

**Relationship**: Can be linked to `users` table (if patient has an account) or exist independently.

---

### 5. **Appointments Table** (`appointments`)
Stores appointment scheduling information.

**Columns:**
- `id` (SERIAL PRIMARY KEY)
- `patient_id` (INTEGER) - Foreign key to `patients.id`
- `doctor_id` (INTEGER) - Foreign key to `doctors.id` (optional)
- `appointment_date` (TIMESTAMP) - Scheduled appointment date/time
- `duration_minutes` (INTEGER) - Appointment duration (default: 30)
- `status` (VARCHAR(50)) - Status: 'scheduled', 'confirmed', 'completed', 'cancelled', 'pending', 'waiting'
- `reason` (TEXT) - Appointment reason/description
- `notes` (TEXT) - Additional notes
- `created_at` (TIMESTAMP) - Record creation time
- `updated_at` (TIMESTAMP) - Last update time

**Purpose**: Manages appointment scheduling. Used in dashboard to show "Today's Appointments" and queue information.

**Relationships**: 
- Many-to-one with `patients` (one patient can have many appointments)
- Many-to-one with `doctors` (one doctor can have many appointments)

---

### 6. **Medical Records Table** (`medical_records`)
Stores patient medical history and treatment records.

**Columns:**
- `id` (SERIAL PRIMARY KEY)
- `patient_id` (INTEGER) - Foreign key to `patients.id`
- `doctor_id` (INTEGER) - Foreign key to `doctors.id` (optional)
- `record_type` (VARCHAR(100)) - Type of record (e.g., 'diagnosis', 'treatment', 'lab_result')
- `diagnosis` (TEXT) - Diagnosis information
- `treatment` (TEXT) - Treatment details
- `medications` (TEXT) - Prescribed medications
- `notes` (TEXT) - Additional notes
- `record_date` (TIMESTAMP) - Date of the medical record
- `created_at` (TIMESTAMP) - Record creation time

**Purpose**: Stores comprehensive medical history for each patient.

**Relationships**: 
- Many-to-one with `patients`
- Many-to-one with `doctors`

---

### 7. **Vitals Table** (`vitals`)
Stores patient vital signs measurements.

**Columns:**
- `id` (SERIAL PRIMARY KEY)
- `patient_id` (INTEGER) - Foreign key to `patients.id`
- `recorded_at` (TIMESTAMP) - When vitals were recorded
- `temperature` (DECIMAL(5,2)) - Body temperature
- `blood_pressure_systolic` (INTEGER) - Systolic BP
- `blood_pressure_diastolic` (INTEGER) - Diastolic BP
- `heart_rate` (INTEGER) - Heart rate (BPM)
- `respiratory_rate` (INTEGER) - Respiratory rate
- `oxygen_saturation` (DECIMAL(5,2)) - SpO2 percentage
- `weight` (DECIMAL(5,2)) - Weight in kg
- `height` (DECIMAL(5,2)) - Height in cm
- `notes` (TEXT) - Additional notes

**Purpose**: Tracks patient vital signs over time. Used in dashboard "Vitals Overview" chart.

**Relationship**: Many-to-one with `patients` (one patient can have many vital records).

---

### 8. **Chatbot Logs Table** (`chatbot_logs`)
Stores chatbot conversation history.

**Columns:**
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER) - Foreign key to `users.id` (optional)
- `patient_id` (INTEGER) - Foreign key to `patients.id` (optional)
- `sender` (VARCHAR(255)) - Sender identifier
- `message` (TEXT) - User message
- `response` (TEXT) - Bot response
- `timestamp` (TIMESTAMP) - Message timestamp

**Purpose**: Logs all chatbot interactions for analysis and "Chatbot Insights" in dashboard.

**Relationships**: Can be linked to `users` or `patients` or exist independently.

---

### 9. **Tasks Table** (`tasks`)
Stores dashboard tasks/to-do items.

**Columns:**
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER) - Foreign key to `users.id`
- `patient_id` (INTEGER) - Foreign key to `patients.id` (optional)
- `title` (VARCHAR(255)) - Task title
- `description` (TEXT) - Task description
- `status` (VARCHAR(50)) - Status: 'pending', 'in_progress', 'completed' (default: 'pending')
- `priority` (VARCHAR(50)) - Priority: 'low', 'medium', 'high' (default: 'medium')
- `due_date` (TIMESTAMP) - Task due date
- `completed_at` (TIMESTAMP) - Completion timestamp
- `created_at` (TIMESTAMP) - Task creation time

**Purpose**: Manages tasks shown in dashboard "Tasks" section.

**Relationships**: 
- Many-to-one with `users` (one user can have many tasks)
- Many-to-one with `patients` (tasks can be linked to specific patients)

---

### 10. **Alerts Table** (`alerts`)
Stores system alerts and notifications.

**Columns:**
- `id` (SERIAL PRIMARY KEY)
- `patient_id` (INTEGER) - Foreign key to `patients.id` (optional)
- `alert_type` (VARCHAR(100)) - Type of alert
- `message` (TEXT) - Alert message
- `severity` (VARCHAR(50)) - Severity: 'low', 'medium', 'high', 'critical' (default: 'medium')
- `is_read` (BOOLEAN) - Whether alert has been read (default: FALSE)
- `created_at` (TIMESTAMP) - Alert creation time

**Purpose**: Manages alerts shown in dashboard "Alerts" card.

**Relationship**: Many-to-one with `patients` (alerts can be linked to specific patients).

---

## Data Flow

### 1. **User Registration & Login**
```
User signs up → users table (email, password_hash, full_name)
User completes profile → user_profiles table (linked via user_id)
User logs in → Authentication via users table → Returns user data
```

### 2. **Patient Data Management**
```
Create patient → patients table
Link to user (optional) → user_id foreign key
Patient data displayed in dashboard → Fetched from patients table
```

### 3. **Dashboard Statistics**
```
Dashboard loads → API calls:
  - GET /api/dashboard/stats → Returns counts from:
    - active_patients: COUNT(patients WHERE status='active')
    - today_appointments: COUNT(appointments WHERE DATE(appointment_date)=TODAY)
    - alerts: COUNT(alerts WHERE is_read=FALSE)
    - queue: COUNT(appointments WHERE status IN ('pending', 'waiting'))
```

### 4. **Appointment Scheduling**
```
Create appointment → appointments table
Link to patient → patient_id foreign key
Link to doctor (optional) → doctor_id foreign key
Display in dashboard → Fetched from appointments table
```

### 5. **Medical Records & Vitals**
```
Record vitals → vitals table (linked to patient_id)
Create medical record → medical_records table (linked to patient_id)
Display in dashboard → Fetched via patient_id
```

---

## API Endpoints

### Authentication
- `POST /auth/signup` - Create new user
- `POST /auth/login` - Authenticate user
- `POST /auth/profile` - Update user profile

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/patients` - Get list of patients
- `GET /api/patients/{patient_id}` - Get specific patient
- `GET /api/appointments` - Get appointments
- `GET /api/tasks` - Get tasks
- `GET /api/patients/{patient_id}/vitals` - Get patient vitals

---

## Frontend Data Display

The Dashboard component (`src/components/Dashboard.jsx`) fetches data from these API endpoints:

1. **On component mount**: Fetches dashboard stats, patients, appointments, and tasks
2. **Displays**:
   - Active Patients count → From `stats.active_patients`
   - Today's Appointments count → From `stats.today_appointments`
   - Alerts count → From `stats.alerts`
   - Queue count → From `stats.queue`
   - Recent Appointments → From `appointments` array
   - Tasks → From `tasks` array

---

## Database Access

All database operations are handled through the `UserDatabase` class in `database.py`:

```python
from database import db

# Example: Get all patients
patients = db.get_all_patients(limit=100, offset=0)

# Example: Get dashboard stats
stats = db.get_dashboard_stats()
```

The class uses connection pooling via context managers to ensure proper connection handling.

---

## Migration from DuckDB

The project was migrated from DuckDB to PostgreSQL. The old DuckDB file (`medwhisper_users.db`) contained only `users` and `user_profiles` tables. All new tables (patients, appointments, etc.) are created automatically in PostgreSQL when the application starts.

---

## Security Considerations

1. **Password Storage**: Passwords are hashed using SHA-256 before storage
2. **SQL Injection Prevention**: All queries use parameterized statements (`%s` placeholders)
3. **Connection Security**: Database credentials stored in `.env` file (not committed to git)
4. **CORS**: API endpoints configured to allow requests from frontend only

---

## Future Enhancements

Potential additions to the schema:
- File uploads table (for medical documents)
- Voice notes table (for audio recordings)
- Analytics/audit logs table
- Notifications table
- Prescriptions table (separate from medical records)

