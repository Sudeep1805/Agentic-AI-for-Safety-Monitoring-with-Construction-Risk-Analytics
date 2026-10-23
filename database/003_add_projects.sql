-- Add authenticated project management to an existing installation.
-- Select the application's database before running. This migration is additive
-- and does not drop, replace, or delete existing tables or rows.
CREATE TABLE IF NOT EXISTS projects (
    id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) NULL,
    description TEXT NULL,
    construction_type VARCHAR(40) NOT NULL,
    project_manager VARCHAR(120) NULL,
    site_address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    pin_code VARCHAR(20) NULL,
    status VARCHAR(20) NOT NULL,
    start_date DATE NULL,
    expected_completion_date DATE NULL,
    budget DECIMAL(15, 2) NULL,
    number_of_workers INTEGER NULL,
    safety_officer VARCHAR(120) NULL,
    safety_notes TEXT NULL,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    INDEX ix_projects_user_id (user_id),
    INDEX ix_projects_user_code (user_id, code),
    CONSTRAINT fk_projects_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
