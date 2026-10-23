-- Reference schema, matching backend/app/models/upload.py.
-- Select your application's database before running. No DROP statements.
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) NOT NULL,
    email VARCHAR(320) NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    password_hash VARCHAR(300) NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS user_sessions (
    id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    token_hash VARCHAR(64) NOT NULL,
    expires_at DATETIME(6) NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_user_sessions_token_hash (token_hash),
    INDEX ix_user_sessions_user_id (user_id),
    CONSTRAINT fk_user_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS site_uploads (
    id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(41) NOT NULL,
    content_type VARCHAR(32) NOT NULL,
    size_bytes INTEGER NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    sha256 VARCHAR(64) NOT NULL,
    site_context TEXT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (stored_filename),
    INDEX ix_site_uploads_created_at (created_at)
    , INDEX ix_site_uploads_user_id (user_id),
    CONSTRAINT fk_site_uploads_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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

CREATE TABLE IF NOT EXISTS detections (
    id INTEGER NOT NULL AUTO_INCREMENT,
    upload_id VARCHAR(36) NOT NULL,
    class_id INTEGER NOT NULL,
    class_name VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    bbox JSON NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    INDEX ix_detections_upload_id (upload_id),
    CONSTRAINT fk_detections_upload FOREIGN KEY (upload_id) REFERENCES site_uploads(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Existing installations: run once after creating users/user_sessions.
-- ALTER TABLE site_uploads ADD COLUMN user_id VARCHAR(36) NULL,
--   ADD INDEX ix_site_uploads_user_id (user_id),
--   ADD CONSTRAINT fk_site_uploads_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
