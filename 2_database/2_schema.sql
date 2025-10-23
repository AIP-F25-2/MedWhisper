-- Core Hospital Tables
CREATE TABLE patients (
  subject_id INTEGER PRIMARY KEY,
  gender VARCHAR,
  anchor_age INTEGER,
  anchor_year INTEGER,
  anchor_year_group VARCHAR,
  dod DATE
);

CREATE TABLE admissions (
  hadm_id INTEGER PRIMARY KEY,
  subject_id INTEGER NOT NULL,
  admittime TIMESTAMP,
  dischtime TIMESTAMP,
  deathtime TIMESTAMP,
  admission_type VARCHAR,
  admission_location VARCHAR,
  discharge_location VARCHAR,
  insurance VARCHAR,
  language VARCHAR,
  marital_status VARCHAR,
  race VARCHAR,
  edregtime TIMESTAMP,
  edouttime TIMESTAMP,
  hospital_expire_flag INTEGER,
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id)
);

CREATE TABLE diagnoses_icd (
  subject_id INTEGER,
  hadm_id INTEGER,
  seq_num INTEGER,
  icd_code VARCHAR,
  icd_version INTEGER,
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (hadm_id) REFERENCES admissions(hadm_id)
);

CREATE TABLE procedures_icd (
  subject_id INTEGER,
  hadm_id INTEGER,
  seq_num INTEGER,
  chartdate DATE,
  icd_code VARCHAR,
  icd_version INTEGER,
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (hadm_id) REFERENCES admissions(hadm_id)
);

CREATE TABLE prescriptions (
  subject_id INTEGER,
  hadm_id INTEGER,
  pharmacy_id BIGINT,
  poe_id BIGINT,
  poe_seq INTEGER,
  starttime TIMESTAMP,
  stoptime TIMESTAMP,
  drug_type VARCHAR,
  drug VARCHAR,
  formulary_drug_cd VARCHAR,
  gsn VARCHAR,
  ndc VARCHAR,
  prod_strength VARCHAR,
  form_rx VARCHAR,
  dose_val_rx VARCHAR,
  dose_unit_rx VARCHAR,
  form_val_disp VARCHAR,
  form_unit_disp VARCHAR,
  doses_per_24_hrs DOUBLE,
  route VARCHAR,
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (hadm_id) REFERENCES admissions(hadm_id)
);

CREATE TABLE labevents (
  labevent_id BIGINT PRIMARY KEY,
  subject_id INTEGER,
  hadm_id INTEGER,
  specimen_id BIGINT,
  itemid INTEGER,
  charttime TIMESTAMP,
  storetime TIMESTAMP,
  value VARCHAR,
  valuenum DOUBLE,
  valueuom VARCHAR,
  ref_range_lower DOUBLE,
  ref_range_upper DOUBLE,
  flag VARCHAR,
  priority VARCHAR,
  comments VARCHAR,
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (hadm_id) REFERENCES admissions(hadm_id)
);

-- Lookups
CREATE TABLE d_labitems (itemid INTEGER PRIMARY KEY, label VARCHAR, fluid VARCHAR, category VARCHAR);
CREATE TABLE d_icd_diagnoses (icd_code VARCHAR, icd_version INTEGER, long_title VARCHAR);
CREATE TABLE d_icd_procedures (icd_code VARCHAR, icd_version INTEGER, long_title VARCHAR);
CREATE TABLE d_hcpcs (code VARCHAR, category INTEGER, long_description VARCHAR, short_description VARCHAR);

-- Optional HOSP ops tables
CREATE TABLE services (subject_id INTEGER, hadm_id INTEGER, transfertime TIMESTAMP, prev_service VARCHAR, curr_service VARCHAR);
CREATE TABLE transfers (subject_id INTEGER, hadm_id INTEGER, transfer_id BIGINT, eventtype VARCHAR, careunit VARCHAR, intime TIMESTAMP, outtime TIMESTAMP);
CREATE TABLE drgcodes (subject_id INTEGER, hadm_id INTEGER, drg_type VARCHAR, drg_code VARCHAR, description VARCHAR, drg_severity INTEGER, drg_mortality INTEGER);

-- Minimal ICU table for later
CREATE TABLE icustays (
  stay_id INTEGER PRIMARY KEY,
  subject_id INTEGER,
  hadm_id INTEGER,
  first_careunit VARCHAR,
  last_careunit VARCHAR,
  intime TIMESTAMP,
  outtime TIMESTAMP,
  los DOUBLE,
  FOREIGN KEY (subject_id) REFERENCES patients(subject_id),
  FOREIGN KEY (hadm_id) REFERENCES admissions(hadm_id)
);
