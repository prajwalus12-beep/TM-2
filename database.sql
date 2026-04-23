-- 1. Employee Table
CREATE TABLE employee (
    employee_id   VARCHAR(50) PRIMARY KEY,
    employee_name VARCHAR(255) NOT NULL,
    slack_id      VARCHAR(100)
);

-- 2. Project Table
CREATE TABLE project (
    id             SERIAL PRIMARY KEY,
    project_code   VARCHAR(50) UNIQUE NOT NULL,
    project_name   VARCHAR(255) NOT NULL,
    lead_engineer  VARCHAR(255),
    priority       VARCHAR(50),
    start_date     DATE,
    end_date       DATE,
    status         VARCHAR(50) DEFAULT 'In progress',
    phase          VARCHAR(100),
    trello_link    TEXT,
    prototype_link TEXT
);

-- 3. Users Table
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    employee_id     VARCHAR(50) UNIQUE REFERENCES employee(employee_id) ON DELETE CASCADE,
    username        VARCHAR(100) UNIQUE NOT NULL,
    password        TEXT NOT NULL,
    failed_attempts INT DEFAULT 0,
    locked_until    TIMESTAMP WITH TIME ZONE
);

-- 4. Timesheet Table
CREATE TABLE timesheet (
    id             SERIAL PRIMARY KEY,
    emp_id         VARCHAR(50) REFERENCES employee(employee_id) ON DELETE CASCADE,
    emp_name       VARCHAR(255),
    project_code   VARCHAR(50) REFERENCES project(project_code) ON DELETE SET NULL,
    project_name   VARCHAR(255),
    date           DATE NOT NULL,
    hours          FLOAT NOT NULL,
    phase          VARCHAR(100),
    project_status VARCHAR(50)
);

-- 5. Project-Employee Assignment Table
CREATE TABLE project_employee (
    employee_id  VARCHAR(50) REFERENCES employee(employee_id) ON DELETE CASCADE,
    project_code VARCHAR(50) REFERENCES project(project_code) ON DELETE CASCADE,
    PRIMARY KEY (employee_id, project_code)
);

-- 6. Project Reports Table (with change tracking)
CREATE TABLE project_reports (
    id                     SERIAL PRIMARY KEY,

    -- Project Code
    project_code           VARCHAR(50) REFERENCES project(project_code) ON DELETE CASCADE,
    project_code_updated   BOOLEAN DEFAULT FALSE,

    -- Project Name
    project_name           VARCHAR(255),
    project_name_updated   BOOLEAN DEFAULT FALSE,

    -- Lead Engineer
    lead_engineer          VARCHAR(255),
    lead_engineer_updated  BOOLEAN DEFAULT FALSE,

    -- Priority
    priority               VARCHAR(50),
    priority_updated       BOOLEAN DEFAULT FALSE,

    -- Start Date
    start_date             DATE,
    start_date_updated     BOOLEAN DEFAULT FALSE,

    -- End Date
    end_date               DATE,
    end_date_updated       BOOLEAN DEFAULT FALSE,

    -- Status
    status                 VARCHAR(50) DEFAULT 'In progress',
    status_updated         BOOLEAN DEFAULT FALSE,

    -- Phase
    phase                  VARCHAR(100),
    phase_updated          BOOLEAN DEFAULT FALSE,

    -- Trello
    trello_link            TEXT,
    trello_link_updated    BOOLEAN DEFAULT FALSE,

    -- Prototype
    prototype_link         TEXT,
    prototype_link_updated BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at             TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at             TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


-- ==========================================
-- STEP 3: AUTO-UPDATE TIMESTAMP TRIGGER
-- ==========================================
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_project_reports_updated_at
BEFORE UPDATE ON project_reports
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();


-- ==========================================
-- STEP 4: INDEXES FOR PERFORMANCE
-- ==========================================
CREATE INDEX idx_timesheet_emp_id          ON timesheet(emp_id);
CREATE INDEX idx_timesheet_project_code    ON timesheet(project_code);
CREATE INDEX idx_timesheet_date            ON timesheet(date);
CREATE INDEX idx_project_status            ON project(status);
CREATE INDEX idx_project_lead_engineer     ON project(lead_engineer);
CREATE INDEX idx_project_reports_code      ON project_reports(project_code);