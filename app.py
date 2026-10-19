#!/usr/bin/env python3
"""
Supervisor Python ringan untuk menjalankan krig-miner sebagai subprocess,
menangani sinyal, healthcheck HTTP lokal, dan restart dengan backoff.
Konfigurasi lewat environment variables:
- MINER_URL (contoh: stratum+ssl://prl-sg.kryptex.network:8048)
- MINER_USER (contoh: mywallet/workername)
- RESTART_MAX (default 5)
- RESTART_BACKOFF (detik, default 5 -> akan double setiap retry)
- HEALTH_PORT (default 8080, bind ke 127.0.0.1)
"""
import os
import signal
import subprocess
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

MINER_BIN = "/usr/local/bin/krig-miner"
MINER_URL = os.getenv("MINER_URL", "stratum+ssl://prl-sg.kryptex.network:8048")
MINER_USER = os.getenv("MINER_USER", "prl1pjp3jd7ue653f6zyrn9ewwu7lalw538kn5w2l4lekv0g3nxqlj23qnwg6g0/olehudin")
RESTART_MAX = int(os.getenv("RESTART_MAX", "5"))
RESTART_BACKOFF = int(os.getenv("RESTART_BACKOFF", "5"))
HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8080"))
HEALTH_HOST = "127.0.0.1"

child_proc = None
shutdown_event = threading.Event()


def log(*args, **kwargs):
    ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
    print(ts, *args, **kwargs)
    sys.stdout.flush()


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/health"):
            self.send_response(404)
            self.end_headers()
            return
        running = child_proc is not None and child_proc.poll() is None
        if running:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK\n")
        else:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"DOWN\n")

    def log_message(self, format, *args):
        # supress default logging
        return


def start_health_server():
    server = HTTPServer((HEALTH_HOST, HEALTH_PORT), HealthHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    log(f"Health server listening on {HEALTH_HOST}:{HEALTH_PORT}")
    return server


def stream_output(proc):
    # baca stdout/stderr gabungan dan print ke stdout container
    for line in iter(proc.stdout.readline, b""):
        if not line:
            break
        try:
            sys.stdout.write(line.decode(errors="replace"))
        except Exception:
            sys.stdout.write(line if isinstance(line, str) else line.decode("utf-8", errors="replace"))
        sys.stdout.flush()


def start_miner():
    args = [
        MINER_BIN,
        "--url", MINER_URL,
        "--user", MINER_USER,
    ]
    log("Starting miner:", " ".join(args))
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1
    )
    # start thread to stream output
    t = threading.Thread(target=stream_output, args=(proc,), daemon=True)
    t.start()
    return proc


def handle_shutdown(signum, frame):
    log("Received signal", signum, "-> shutting down")
    shutdown_event.set()
    if child_proc and child_proc.poll() is None:
        try:
            log("Sending SIGTERM to miner pid", child_proc.pid)
            child_proc.terminate()
            # tunggu sebentar
            for _ in range(10):
                if child_proc.poll() is not None:
                    break
                time.sleep(1)
            if child_proc.poll() is None:
                log("Miner did not exit -> killing")
                child_proc.kill()
        except Exception as e:
            log("Error shutting down miner:", e)


def main():
    global child_proc
    if not os.path.exists(MINER_BIN) or not os.access(MINER_BIN, os.X_OK):
        log("Miner binary not found or not executable:", MINER_BIN)
        sys.exit(1)

    # register signals
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    health = start_health_server()

    retries = 0
    backoff = RESTART_BACKOFF

    while not shutdown_event.is_set():
        child_proc = start_miner()
        # tunggu sampai child exit atau kami diminta shutdown
        while True:
            if shutdown_event.is_set():
                break
            ret = child_proc.poll()
            if ret is not None:
                log("Miner exited with code", ret)
                break
            time.sleep(1)

        if shutdown_event.is_set():
            break

        # jika miner keluar dengan sendirinya -> restart logic
        retries += 1
        if RESTART_MAX >= 0 and retries > RESTART_MAX:
            log("Exceeded max restart attempts:", RESTART_MAX)
            break
        log(f"Restarting miner in {backoff}s (attempt {retries}/{RESTART_MAX})")
        time.sleep(backoff)
        backoff = min(300, backoff * 2)

    # cleanup
    try:
        health.shutdown()
    except Exception:
        pass

    if child_proc and child_proc.poll() is None:
        try:
            child_proc.terminate()
        except Exception:
            pass

    log("Supervisor exiting")
    sys.exit(0)


if __name__ == "__main__":
    main()
