import json
import os
import glob
import psycopg2
from psycopg2.extras import execute_values

DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "timlul_db"),
    "user": os.getenv("POSTGRES_USER", "timlul_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "timlul_password"),
    "host": os.getenv("DB_HOST", "postgres"),
    "port": os.getenv("DB_PORT", "5432")
}

def process_json_file(file_path):
    print(f"Processing: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if isinstance(data, dict):
        data = [data]

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    query = """
    INSERT INTO transcription_jobs (
        job_id, user_principal, display_name, started_at, gemini_sent_at, finished_at,
        filename, file_extension, status, audio_duration_seconds, transcription_seconds,
        gemini_processing_seconds, total_processing_seconds, input_tokens, output_tokens,
        thinking_tokens, billable_output_tokens, total_tokens, estimated_input_cost_usd,
        estimated_output_cost_usd, estimated_total_cost_usd, israeli_id_count,
        card_number_count, phone_number_count, vehicle_number_count, email_count,
        passport_count, last_name_count, address_count, sensitive_data_total
    ) VALUES %s
  ON CONFLICT (job_id) DO UPDATE SET
        user_principal = EXCLUDED.user_principal,
        display_name = EXCLUDED.display_name,
        status = EXCLUDED.status,
        finished_at = EXCLUDED.finished_at;
    """
    
    records = []
    for job in data:
        filename = job.get("filename", "")
        ext = os.path.splitext(filename)[1].lower() if filename else ""
        usage = job.get("gemini_usage", {})
        pii = job.get("sensitive_data", {})
        
        records.append((
            job["job_id"],
            job.get("user"),
            job.get("display_name"),
            job.get("started_at"),
            job.get("gemini_sent_at"),
            job.get("finished_at"),
            filename,
            ext,
            job.get("status", "success"),
            job.get("audio_duration_seconds"),
            job.get("transcription_seconds"),
            job.get("gemini_processing_seconds"),
            job.get("total_processing_seconds"),
            usage.get("input_tokens", 0),
            usage.get("output_tokens", 0),
            usage.get("thinking_tokens", 0),
            usage.get("billable_output_tokens", 0),
            usage.get("total_tokens", 0),
            usage.get("estimated_input_cost_usd", 0),
            usage.get("estimated_output_cost_usd", 0),
            usage.get("estimated_total_cost_usd", 0),
            pii.get("israeli_id", 0),
            pii.get("card_number", 0),
            pii.get("phone_number", 0),
            pii.get("vehicle_number", 0),
            pii.get("email", 0),
            pii.get("passport", 0),
            pii.get("last_name", 0),
            pii.get("address", 0),
            job.get("sensitive_data_total", 0)
        ))
        
    if records:
        execute_values(cur, query, records)
        conn.commit()
        print(f"Successfully inserted/updated {len(records)} jobs.")
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    json_files = glob.glob("./*.json")
    for file in json_files:
        process_json_file(file)