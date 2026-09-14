import psycopg2
import os

DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "timlul_db"),
    "user": os.getenv("POSTGRES_USER", "timlul_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "timlul_password"),
    "host": os.getenv("DB_HOST", "postgres"),
    "port": os.getenv("DB_PORT", "5432")
}

def init_db():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transcription_jobs (
        job_id VARCHAR(64) PRIMARY KEY,
        user_principal VARCHAR(128),
        display_name VARCHAR(128),
        started_at TIMESTAMPTZ,
        gemini_sent_at TIMESTAMPTZ,
        finished_at TIMESTAMPTZ,
        filename VARCHAR(255),
        file_extension VARCHAR(10),
        status VARCHAR(32) DEFAULT 'success',
        
        -- Performance Metrics
        audio_duration_seconds NUMERIC(10, 2),
        transcription_seconds NUMERIC(10, 3),
        gemini_processing_seconds NUMERIC(10, 3),
        total_processing_seconds NUMERIC(10, 2),
        
        -- Gemini Usage
        input_tokens INT,
        output_tokens INT,
        thinking_tokens INT,
        billable_output_tokens INT,
        total_tokens INT,
        estimated_input_cost_usd NUMERIC(10, 6),
        estimated_output_cost_usd NUMERIC(10, 6),
        estimated_total_cost_usd NUMERIC(10, 6),
        
        -- Sensitive Data (PII)
        israeli_id_count INT DEFAULT 0,
        card_number_count INT DEFAULT 0,
        phone_number_count INT DEFAULT 0,
        vehicle_number_count INT DEFAULT 0,
        email_count INT DEFAULT 0,
        passport_count INT DEFAULT 0,
        last_name_count INT DEFAULT 0,
        address_count INT DEFAULT 0,
        sensitive_data_total INT DEFAULT 0,

        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_jobs_started_at ON transcription_jobs(started_at);
    CREATE INDEX IF NOT EXISTS idx_jobs_user ON transcription_jobs(user_principal);
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("PostgreSQL Database initialized successfully.")

if __name__ == "__main__":
    init_db()