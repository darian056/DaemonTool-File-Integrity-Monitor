import recursive_monitor
import hashlib
from pathlib import Path
from colorama import Fore, Back, Style, init
import logging
from rich.console import Console
import time



def Calculate_File_hash(path):
    with open(path, "rb") as f:
        digest = hashlib.file_digest(f, "sha256")

    file_hash = digest.hexdigest()
    f_path_hash = str(Path(path).resolve()) + " | " + file_hash + "\n"

    return f_path_hash


def Logs(path, event=None):
    log_dir = Path("fim_Logs")
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
    filename=log_dir / 'dev.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(process)d %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')

    resolved_path = Path(path).resolve()

    if event == "DELETED":
        message = f"{event} | {resolved_path}"
    else:
        message = f"{event} | {resolved_path}" 

    logging.info(message)

def option_a(b_path):

        b_path.parent.mkdir(exist_ok=True)

        if b_path.exists():
            b_path.unlink()

        p = Path.cwd()
        data_dir = p / "fim_data"
        log_dir = p / "fim_Logs"

        with open(b_path, "a") as basefile:
            for f in p.rglob("*"):

                if f.is_relative_to(data_dir):
                    continue
                elif f.is_relative_to(log_dir):
                    continue
                else:
                    if f.is_file():
                        basefile.write(Calculate_File_hash(f))




def option_b(b_path):
    fileHashDict = {}
    p = Path.cwd()
    logs_dir = p / "fim_Logs"   
    data_dir = p / "fim_data"

    
    with open(b_path, "r") as file:
        for f in p.rglob("*"):
            if f.is_relative_to(data_dir):
                continue
            elif f.is_relative_to(logs_dir):
                continue
        for line in file:
            parts = line.strip().split(" | ")
            if len(parts) == 2:
                fileHashDict[str(Path(parts[0]).resolve())] = parts[1]

    recursive_monitor.start_fim_daemon()


if __name__ == "__main__":
    init(autoreset=True)

    print(
        Fore.YELLOW
        + r"""  / __\  __  / __  ___
 / _\   / / / /  \/   \
/ /    / / / /  / /\/\ \
\/    /_/ /_/  /\/    \/"""
    )

    print(Fore.LIGHTMAGENTA_EX + "\nFile Monitoring Daemon\nBuilt by Darian Dsouza\n")
    print(Fore.CYAN + "-" * 42)
    print(
        Fore.WHITE
        + "[A] Collect new Baseline\n"
        + "[B] Begin monitoring files with saved Baseline\n"
        + Fore.LIGHTBLACK_EX
        + "Press 'e' to exit when running\n"
    )

    userin = input(Fore.YELLOW + ">> " + Style.RESET_ALL).strip().lower()

    path = Path.cwd()
    b_path = path / "fim_data" / "baseline.txt"

    if userin == "a":
        option_a(b_path)
        console = Console()
        with console.status("[bold cyan]Sorting through files & creating baseline...[/bold cyan]"):
            time.sleep(2)
        option_b(b_path)
    elif userin == "b":
        option_b(b_path)