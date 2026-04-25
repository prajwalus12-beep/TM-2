-- Timesheet Application Database Schema
-- Compatible with PostgreSQL / Supabase

-- 1. Employee Table
CREATE TABLE IF NOT EXISTS employee (
    employee_id VARCHAR(50) PRIMARY KEY,
    employee_name VARCHAR(255) NOT NULL,
    slack_id VARCHAR(100)
);

-- 2. Project Table
CREATE TABLE IF NOT EXISTS project (
    project_code VARCHAR(50) PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL, -- Encrypted in application logic
    status VARCHAR(50) DEFAULT 'In progress',
    priority VARCHAR(50),
    lead_engineer VARCHAR(255),
    trello_link TEXT
);

-- 3. Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) UNIQUE REFERENCES employee(employee_id) ON DELETE CASCADE,
    username VARCHAR(100) UNIQUE NOT NULL,
    password TEXT NOT NULL, -- Encrypted/Hashed in application logic
    failed_attempts INT DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE
);

-- 4. Timesheet Table
CREATE TABLE IF NOT EXISTS timesheet (
    id SERIAL PRIMARY KEY,
    emp_id VARCHAR(50) REFERENCES employee(employee_id) ON DELETE CASCADE,
    emp_name VARCHAR(255), -- Denormalized for convenience
    project_code VARCHAR(50) REFERENCES project(project_code) ON DELETE SET NULL,
    project_name VARCHAR(255), -- Denormalized and Encrypted
    date DATE NOT NULL,
    hours FLOAT NOT NULL,
    "Phase" VARCHAR(20),
    project_status VARCHAR(50)
);

-- 5. Project-Employee Assignment Table (Junction)
CREATE TABLE IF NOT EXISTS project_employee (
    employee_id VARCHAR(50) REFERENCES employee(employee_id) ON DELETE CASCADE,
    project_code VARCHAR(50) REFERENCES project(project_code) ON DELETE CASCADE,
    PRIMARY KEY (employee_id, project_code)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_timesheet_emp_id ON timesheet(emp_id);
CREATE INDEX IF NOT EXISTS idx_timesheet_project_code ON timesheet(project_code);
CREATE INDEX IF NOT EXISTS idx_timesheet_date ON timesheet(date);

-- Note: Admin user is typically initialized via the application's init_db() function.
-- The following are manual initialization snippets if needed:
/*
INSERT INTO employee (employee_id, employee_name) 
VALUES ('admin', 'System Administrator')
ON CONFLICT (employee_id) DO NOTHING;

INSERT INTO users (employee_id, username, password)
VALUES ('admin', 'admin', 'YOUR_ENCRYPTED_PASSWORD_HERE')
ON CONFLICT (username) DO NOTHING;
*/

-- ==========================================
-- UPDATE SCRIPT TO ADD NEW PROJECT COLUMNS
-- Run this manually in Supabase SQL Editor:
-- ==========================================
-- ALTER TABLE project 
-- ADD COLUMN priority VARCHAR(50),
-- ADD COLUMN lead_engineer VARCHAR(255),
-- ADD COLUMN trello_link TEXT;
