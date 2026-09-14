import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ingest_json import process_json_file

WATCH_DIRECTORY = "./"

class JsonHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            time.sleep(0.5) 
            print(f"[Real-Time] קובץ חדש זוהה: {event.src_path}")
            process_json_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            time.sleep(0.5)
            print(f"[Real-Time] קובץ עודכן: {event.src_path}")
            process_json_file(event.src_path)

if __name__ == "__main__":
    event_handler = JsonHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCH_DIRECTORY, recursive=False)
    observer.start()
    print(f"מערכת ניטור בזמן אמת פעילה על התיקייה: {os.path.abspath(WATCH_DIRECTORY)}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
