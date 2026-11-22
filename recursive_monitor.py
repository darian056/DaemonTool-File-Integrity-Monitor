import baselineengine
from pathlib import Path
import time
from colorama import Fore, Back, Style, init
from watchdog.events import FileSystemEvent, FileSystemEventHandler, LoggingEventHandler
from watchdog.observers import Observer
from rich.console import Console
import msvcrt
import threading
import json


class MyEventHandler(FileSystemEventHandler):
    def __init__(self, config_path = "config.JSON"):
        super().__init__()
        p = Path.cwd()
        self.logs_dir = (p / "fim_Logs").resolve()
        self.data_dir = (p / "fim_data").resolve()
        self.last_events = {} #keeps track of all of the events taking place all while the daemon is running and flushes once exited
        with open (Path(config_path), "r", encoding="utf-8") as f:
            self.config = json.load(f)
        self.extmap = self.config.get("severity_by_extension", {})
        self.delextmap = self.config.get("deleted_severity_by_extension", {})
        self.default_sev = self.config.get("default_severity", "LOW")

    def should_ignore(self, p):
        resolved_path = Path(p).resolve()

        if resolved_path.is_relative_to(self.data_dir) or resolved_path.is_relative_to(self.logs_dir):
            return True
        return False

# created this because of duplicated alerts in the dev.logs file as well as the terminal alerts
    def is_debounce(self, p):
        current_time = time.time() #showing the current time
        resolved_path = Path(p).resolve() #current path we are in

        if resolved_path in self.last_events: #checks the dictionary if this path already exists
            if current_time - self.last_events[resolved_path] < 1.5: #checks the value of the path which is the current time, if the current time - logged time whenever it happened is less than 1.5 seconds its detecting two changes in the os so it discounts the second one beingmade to remove any duplicate logs and alerts
                return True
        self.last_events[resolved_path] = current_time #assigning the key and value
        print(self.last_events) # just a test print so I can see whats actually happening
        return False


    def on_modified(self, event):
        if event.is_directory or self.should_ignore(event.src_path) or self.is_debounce(event.src_path):
            return
        print(Fore.BLUE+f"File modified: {event.src_path}")
        baselineengine.Logs(event.src_path, "MODIFIED")


    def on_created(self, event):
        if event.is_directory or self.should_ignore(event.src_path):
            return
        ext = Path(event.src_path).suffix.lower()
        severity = self.extmap.get(ext, self.default_sev)
        print(Fore.GREEN+f"Severity: {severity} | File created: {event.src_path}")
        baselineengine.Logs(event.src_path, "CREATED")

    def on_deleted(self, event):
        if event.is_directory or self.should_ignore(event.src_path):
            return
        ext = Path(event.src_path).suffix.lower()
        severity = self.delextmap.get(ext, self.default_sev)
        print(Fore.RED+f"Severity: {severity} | File deleted: {event.src_path}")
        baselineengine.Logs(event.src_path, "DELETED")


console = Console() #simple CLI loading animation class object


def _watch_terminal_exit(exit_event: threading.Event):
    while not exit_event.is_set():
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch and ch.casefold() == "e":
                exit_event.set()
                break
        time.sleep(0.1)

def start_fim_daemon():
    try:
        event_handler = MyEventHandler()
        w_path_i = Path.cwd()
        w_path = w_path_i.resolve()
        b_path = w_path / "fim_data" / "baseline.txt"
        observer = Observer()
        observer.schedule(event_handler, path=str(w_path), recursive=True)
        observer.start()
        exit_requested = threading.Event()
        key_thread = threading.Thread(
        target=_watch_terminal_exit,
        args=(exit_requested,),
        daemon=True)
        key_thread.start()

        with console.status(Fore.CYAN+"FIM Background Daemon running..."):
            while not exit_requested.is_set():
                time.sleep(0.5)
        with console.status(Fore.RED + "Exiting.."):
            time.sleep(1)
        with console.status(Fore.GREEN+"Backing up baseline"):
            time.sleep(1)
        baselineengine.option_a(b_path)

    except KeyboardInterrupt:
        print(Fore.RED+f"Error occurred: KeyboardInterrupt")
        with console.status(Fore.RED+"Stopping Daemon.."):
            time.sleep(1)
    finally:
        exit_requested.set()
        observer.stop()
        observer.join()