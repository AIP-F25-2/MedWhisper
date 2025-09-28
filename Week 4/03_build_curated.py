import duckdb

con = duckdb.connect("medwhisper.db")

con.execute("""
-- Patients (patients.csv HAS Id)
CREATE OR REPLACE TABLE patients_curated AS
SELECT
  Id           AS patient_id,
  GENDER       AS gender,
  BIRTHDATE    AS birthdate,
  DEATHDATE    AS deathdate,
  RACE         AS race,
  ETHNICITY    AS ethnicity,
  ADDRESS      AS address,
  CITY         AS city,
  STATE        AS state,
  ZIP          AS zip
FROM raw_patients;

-- Encounters (encounters.csv HAS Id)
CREATE OR REPLACE TABLE encounters_curated AS
SELECT
  Id               AS encounter_id,
  PATIENT          AS patient_id,
  START            AS start_time,
  STOP             AS end_time,
  ENCOUNTERCLASS   AS encounter_class,
  CAST(CODE AS VARCHAR) AS code,
  DESCRIPTION      AS description,
  PROVIDER         AS provider
FROM raw_encounters;

-- Conditions (NO Id in conditions.csv) → synthesize IDs
CREATE OR REPLACE TABLE conditions_curated AS
SELECT
  CONCAT('cond_', ROW_NUMBER() OVER ())              AS condition_id,
  PATIENT                                            AS patient_id,
  ENCOUNTER                                          AS encounter_id,
  CAST(CODE AS VARCHAR)                              AS code,
  DESCRIPTION                                        AS description,
  TRY_CAST(START AS DATE)                            AS onset_date,
  TRY_CAST(STOP  AS DATE)                            AS abatement_date,
  NULL                                               AS clinical_status
FROM raw_conditions;

-- Procedures (NO Id in procedures.csv) → synthesize IDs
CREATE OR REPLACE TABLE procedures_curated AS
SELECT
  CONCAT('proc_', ROW_NUMBER() OVER ())              AS procedure_id,
  PATIENT                                            AS patient_id,
  ENCOUNTER                                          AS encounter_id,
  CAST(CODE AS VARCHAR)                              AS code,
  DESCRIPTION                                        AS description,
  TRY_CAST(START AS TIMESTAMP)                       AS performed_at
FROM raw_procedures;

-- Medications (NO Id in medications.csv) → synthesize IDs
CREATE OR REPLACE TABLE medications_curated AS
SELECT
  CONCAT('med_', ROW_NUMBER() OVER ())               AS medication_id,
  PATIENT                                            AS patient_id,
  ENCOUNTER                                          AS encounter_id,
  CAST(CODE AS VARCHAR)                              AS code,
  DESCRIPTION                                        AS description,
  TRY_CAST(START AS DATE)                            AS start_date,
  TRY_CAST(STOP  AS DATE)                            AS end_date,
  NULL                                               AS status
FROM raw_medications;

-- Observations (NO Id in observations.csv) → synthesize IDs
CREATE OR REPLACE TABLE observations_curated AS
SELECT
  CONCAT('obs_', ROW_NUMBER() OVER ())               AS observation_id,
  PATIENT                                            AS patient_id,
  ENCOUNTER                                          AS encounter_id,
  CAST(CODE AS VARCHAR)                              AS code,
  DESCRIPTION                                        AS description,
  CAST(VALUE AS VARCHAR)                             AS value,
  UNITS                                              AS unit,
  TRY_CAST(DATE AS TIMESTAMP)                        AS observed_at
FROM raw_observations;

-- Unified timeline view built from curated tables (replaces any previous)
CREATE OR REPLACE VIEW timeline_events AS
SELECT patient_id, start_time    AS event_time, 'encounter'         AS event_type, encounter_id  AS event_id, description FROM encounters_curated
UNION ALL
SELECT patient_id, performed_at  AS event_time, 'procedure'         AS event_type, procedure_id  AS event_id, description FROM procedures_curated
UNION ALL
SELECT patient_id, CAST(start_date AS TIMESTAMP) AS event_time, 'medication_start' AS event_type, medication_id AS event_id, description FROM medications_curated
UNION ALL
SELECT patient_id, observed_at   AS event_time, 'observation'       AS event_type, observation_id AS event_id, description FROM observations_curated
UNION ALL
SELECT patient_id, CAST(onset_date AS TIMESTAMP) AS event_time, 'condition_onset' AS event_type, condition_id AS event_id, description FROM conditions_curated WHERE onset_date IS NOT NULL
UNION ALL
SELECT patient_id, CAST(abatement_date AS TIMESTAMP) AS event_time, 'condition_end' AS event_type, condition_id AS event_id, description FROM conditions_curated WHERE abatement_date IS NOT NULL;
""")

print("Curated tables built and timeline view refreshed.")
