# Transcription Analytics Dashboard

A containerized full-stack analytics platform built with Streamlit, PostgreSQL, and Docker to monitor transcription workloads, evaluate Gemini model token usage and operational costs, and audit detected Personally Identifiable Information (PII) in real time.

---

## Key Features

* **Interactive Executive Dashboard:** Native Right-to-Left (RTL) Hebrew UI with dynamic filtering by date ranges, specific users, or custom text search.
* **PII & Data Redaction Tracking:** Real-time visibility into scrubbed entities (Israeli IDs, credit cards, phones, vehicle plates, emails, addresses, and passports).
* **Gemini LLM Cost & Token Monitoring:** Granular insights into input, output, and thinking token consumption alongside calculated operational costs.
* **Real-Time Data Ingestion:** Automated filesystem watcher powered by `watchdog` that listens for new transcription JSON files and batches them directly into PostgreSQL.
* **Containerized Architecture:** Fully reproducible environment orchestrated with Docker and Docker Compose.

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
