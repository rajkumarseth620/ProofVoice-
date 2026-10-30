-- ProofVoice MySQL Database Initialization Script
-- Run this as MySQL root user:
--   mysql -u root -p < init_db.sql

CREATE DATABASE IF NOT EXISTS proofvoice_db 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- Note: Replace 'your_secure_password_here' with the actual password configured in backend/.env DB_PASSWORD
CREATE USER IF NOT EXISTS 'proofvoice_user'@'localhost' IDENTIFIED BY 'your_secure_password_here';
CREATE USER IF NOT EXISTS 'proofvoice_user'@'127.0.0.1' IDENTIFIED BY 'your_secure_password_here';

GRANT ALL PRIVILEGES ON proofvoice_db.* TO 'proofvoice_user'@'localhost';
GRANT ALL PRIVILEGES ON proofvoice_db.* TO 'proofvoice_user'@'127.0.0.1';

FLUSH PRIVILEGES;

SHOW DATABASES LIKE 'proofvoice_db';
