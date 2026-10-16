import sys
import time
import atexit
import socket
import threading
import subprocess
from pathlib import Path

import truststore
truststore.inject_into_ssl()

import webview


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def wait_for_port(port, host='127.0.0.1', timeout=30.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.3)
    return False


def cleanup():
    global process
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()


def setup_signal_handlers():
    if threading.current_thread() is threading.main_thread():
        try:
            import signal
            def signal_handler(sig, frame):
                sys.exit(0)
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except (ValueError, OSError):
            pass


setup_signal_handlers()

atexit.register(cleanup)


process = None

def run_launcher(script_folder: str | Path):
    global process
    
    port = get_free_port()

    script_folder = Path(script_folder)
    script_path = script_folder / "launcher_page.py"

    if sys.platform == 'win32':
        icon_path = script_folder / "static/logo.ico"
        gui_engine = 'edgechromium'
    elif sys.platform == 'darwin':
        icon_path = script_folder / "static/logo.icns"
        gui_engine = 'cocoa'
    else:
        icon_path = script_folder / "static/logo.png"
        gui_engine = 'gtk'

    cmd = [
        sys.executable, 
        "__run_streamlit__", 
        str(script_path), 
        str(port)
    ]

    log_file_path = Path("streamlit.log")
    log_file = open(log_file_path, "w", encoding="utf-8")

    process = subprocess.Popen(cmd, 
                               stdout=log_file,
                               stderr=subprocess.STDOUT, 
                               text=True,
                               encoding='utf-8'
                               )

    if not wait_for_port(port):
        print("Streamlit не запустился вовремя. Смотрите streamlit.log")
        process.kill()
        log_file.close()
        sys.exit(1)
    
    log_file.close()

    url = f"http://localhost:{port}"
    
    webview.create_window('Индексатор научных публикаций', url, width=1024, height=768)
    webview.start(gui=gui_engine, icon=str(icon_path) if icon_path else None)