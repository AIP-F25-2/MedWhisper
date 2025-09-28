PRAGMA enable_verification;

-- Patients
CREATE TABLE IF NOT EXISTS patients (
    patient_id       VARCHAR PRIMARY KEY,
    gender           VARCHAR,
    birthdate        DATE,
    deathdate        DATE,
    race             VARCHAR,
    ethnicity        VARCHAR,
    address          VARCHAR,
    city             VARCHAR,
    state            VARCHAR,
    zip              VARCHAR
);

-- Encounters (timeline backbone)
CREATE TABLE IF NOT EXISTS encounters (
    encounter_id     VARCHAR PRIMARY KEY,
    patient_id       VARCHAR,
    start_time       TIMESTAMP,
    end_time         TIMESTAMP,
    encounter_class  VARCHAR,
    code             VARCHAR,
    description      VARCHAR,
    provider         VARCHAR
);

-- Conditions
CREATE TABLE IF NOT EXISTS conditions (
    condition_id     VARCHAR PRIMARY KEY,
    patient_id       VARCHAR,
    encounter_id     VARCHAR,
    code             VARCHAR,
    description      VARCHAR,
    onset_date       DATE,
    abatement_date   DATE,
    clinical_status  VARCHAR
);

-- Procedures
CREATE TABLE IF NOT EXISTS procedures (
    procedure_id     VARCHAR PRIMARY KEY,
    patient_id       VARCHAR,
    encounter_id     VARCHAR,
    code             VARCHAR,
    description      VARCHAR,
    performed_at     TIMESTAMP
);

-- Medications
CREATE TABLE IF NOT EXISTS medications (
    medication_id    VARCHAR PRIMARY KEY,
    patient_id       VARCHAR,
    encounter_id     VARCHAR,
    code             VARCHAR,
    description      VARCHAR,
    start_date       DATE,
    end_date         DATE,
    status           VARCHAR
);

-- Observations (labs/vitals)
CREATE TABLE IF NOT EXISTS observations (
    observation_id   VARCHAR PRIMARY KEY,
    patient_id       VARCHAR,
    encounter_id     VARCHAR,
    code             VARCHAR,
    description      VARCHAR,
    value            VARCHAR,
    unit             VARCHAR,
    observed_at      TIMESTAMP
);

-- Reports (clinical notes)
CREATE TABLE IF NOT EXISTS reports (
    report_id        VARCHAR PRIMARY KEY,
    patient_id       VARCHAR,
    encounter_id     VARCHAR,
    report_type      VARCHAR,
    report_text      TEXT,
    created_at       TIMESTAMP
);

-- Transcripts (Whisper output)
CREATE TABLE IF NOT EXISTS transcripts (
    transcript_id    VARCHAR PRIMARY KEY,
    patient_id       VARCHAR,
    encounter_id     VARCHAR,
    media_path       VARCHAR,
    transcript_text  TEXT,
    language         VARCHAR,
    duration_seconds INTEGER,
    source           VARCHAR,
    created_at       TIMESTAMP
);

-- Images (for CLIP)
CREATE TABLE IF NOT EXISTS images (
    image_id         VARCHAR PRIMARY KEY,
    patient_id       VARCHAR,
    encounter_id     VARCHAR,
    image_path       VARCHAR,
    modality         VARCHAR,
    width_px         INTEGER,
    height_px        INTEGER,
    created_at       TIMESTAMP
);

-- Feedback (quality loop)
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id      VARCHAR PRIMARY KEY,
    session_id       VARCHAR,
    user_id          VARCHAR,
    query_text       TEXT,
    rating           INTEGER,
    comments         TEXT,
    created_at       TIMESTAMP
);

-- Audit (compliance/debug)
CREATE TABLE IF NOT EXISTS audit (
    audit_id         VARCHAR PRIMARY KEY,
    ts               TIMESTAMP,
    actor            VARCHAR,
    action           VARCHAR,
    resource_type    VARCHAR,
    resource_id      VARCHAR,
    metadata_json    VARCHAR
);

-- One unified timeline view (broad; includes reports/transcripts/images)
CREATE OR REPLACE VIEW timeline_events AS
SELECT patient_id, start_time AS event_time, 'encounter' AS event_type, encounter_id AS event_id, description
FROM encounters
UNION ALL
SELECT patient_id, performed_at, 'procedure', procedure_id, description
FROM procedures
UNION ALL
SELECT patient_id, CAST(start_date AS TIMESTAMP), 'medication_start', medication_id, description
FROM medications
UNION ALL
SELECT patient_id, observed_at, 'observation', observation_id, description
FROM observations
UNION ALL
SELECT patient_id, created_at, 'report', report_id, report_type || ' note'
FROM reports
UNION ALL
SELECT patient_id, created_at, 'transcript', transcript_id, source || ' audio transcript'
FROM transcripts
UNION ALL
SELECT patient_id, created_at, 'image', image_id, modality || ' image'
FROM images;
