# Transcription Analytics Dashboard

A containerized full-stack analytics platform built with Streamlit, PostgreSQL, and Docker to monitor transcription workloads, evaluate Gemini model token usage and operational costs, and audit detected Personally Identifiable Information (PII) in real time[cite: 3, 4, 8].

---

## Key Features

* **Interactive Executive Dashboard:** Native Right-to-Left (RTL) Hebrew UI with dynamic filtering by date ranges, specific users, or custom text search[cite: 3].
* **PII & Data Redaction Tracking:** Real-time visibility into scrubbed entities (Israeli IDs, credit cards, phones, vehicle plates, emails, addresses, and passports)[cite: 3, 8].
* **Gemini LLM Cost & Token Monitoring:** Granular insights into input, output, and thinking token consumption alongside calculated operational costs[cite: 3, 8].
* **Real-Time Data Ingestion:** Automated filesystem watcher powered by `watchdog` that listens for new transcription JSON files and batches them directly into PostgreSQL[cite: 6, 7].
* **Containerized Architecture:** Fully reproducible environment orchestrated with Docker and Docker Compose[cite: 4, 5].

---

## Architecture Overview

```text
[ Transcription JSON Files ]
             │
             ▼
[ File Watcher Daemon (Watchdog) ] ──► [ Ingestion Pipeline ] ──► [ PostgreSQL 15 ]
                                                                        │
                                                                        ▼
                                                           [ Streamlit Dashboard (RTL) ]
```

---

## Quick Start

### 1. Environment Configuration
Copy the example environment file and configure credentials if needed[cite: 1]:
```bash
cp .env.example .env
```

### 2. Build and Run with Docker Compose
Start the PostgreSQL database and dashboard services[cite: 4, 5]:
```bash
docker compose up -d --build
```

### 3. Access the Dashboard
Open your browser and navigate to[cite: 1, 3]:
```text
http://localhost:8501
```

### 4. Monitor Container Logs
To inspect ingestion activity and operational logs:
```bash
docker logs -f timlul_dashboard
```

---

## Configuring the Ingestion Directory

By default, the ingestion engine monitors the container's root working directory (`./`) for top-level `*.json` files[cite: 6, 7]. If you want to customize the ingestion path (e.g., to `./data` or an external directory on the host), update the following three files:

### 1. File Watcher Daemon (`file_watcher.py`)
Update `WATCH_DIRECTORY` and enable recursive monitoring if you need to detect files in nested subfolders[cite: 6]:
```python
# file_watcher.py
WATCH_DIRECTORY = "./data"  # Set to your target directory path

# In main block: set recursive=True to scan subdirectories
observer.schedule(event_handler, path=WATCH_DIRECTORY, recursive=True)
```

### 2. Startup Batch Loader (`ingest_json.py`)
Update the `glob` file pattern executed during container initialization[cite: 7]:
```python
# ingest_json.py
if __name__ == "__main__":
    json_files = glob.glob("./data/*.json")  # Match the new path/pattern
    for file in json_files:
        process_json_file(file)
```

### 3. Volume Mounting (`docker-compose.yml`)
Ensure the host path is mounted to the container directory under the `dashboard` service[cite: 4]:
```yaml
services:
  dashboard:
    # ...
    volumes:
      - ./data:/app/data        # Map host folder to container folder
      - /app/__pycache__
```

After modifying the configuration, restart the environment:
```bash
docker compose down
docker compose up -d
```

---

## Expected JSON Schema

The ingestion pipeline expects structured transcription JSON payloads matching the following schema[cite: 7, 8]:

```json
{
  "job_id": "job-test-2026-09-14-001",
  "user": "ser@example.com",
  "display_name": "Transcription User",
  "started_at": "2026-09-14T10:00:00Z",
  "gemini_sent_at": "2026-09-14T10:02:10Z",
  "finished_at": "2026-09-14T10:03:30Z",
  "filename": "customer_call.mp3",
  "status": "success",
  "audio_duration_seconds": 360.5,
  "transcription_seconds": 130.0,
  "gemini_processing_seconds": 80.0,
  "total_processing_seconds": 210.0,
  "gemini_usage": {
    "input_tokens": 5420,
    "output_tokens": 1280,
    "thinking_tokens": 450,
    "billable_output_tokens": 1280,
    "total_tokens": 7150,
    "estimated_input_cost_usd": 0.00271,
    "estimated_output_cost_usd": 0.00384,
    "estimated_total_cost_usd": 0.00655
  },
  "sensitive_data": {
    "israeli_id": 2,
    "card_number": 1,
    "phone_number": 3,
    "vehicle_number": 0,
    "email": 1,
    "passport": 0,
    "last_name": 4,
    "address": 1
  },
  "sensitive_data_total": 12
}
```

---

## Troubleshooting

* **Port 8501 Already Allocated (`Bind for 0.0.0.0:8501 failed`):**
  Stray containers or background instances might still bind port 8501[cite: 1, 3]. Clear orphan containers:
  ```bash
  docker compose down --remove-orphans
  ```
* **New Files Not Showing on Dashboard:**
  1. Confirm the file has a `.json` extension and is valid non-empty JSON[cite: 6, 7].
  2. Ensure the host path containing the file is mapped in `docker-compose.yml` under `volumes`[cite: 4].
  3. Inspect container logs for real-time trigger messages[cite: 6, 7]:
     ```bash
     docker logs -f timlul_dashboard
     ```
  4. Verify the dashboard sidebar filter matches the date range of the ingested job[cite: 3].
