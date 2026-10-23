-- Add persisted YOLO detections to an existing installation.
-- Select the application's database before running. This migration is additive
-- and does not drop, replace, or delete existing tables or rows.
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
