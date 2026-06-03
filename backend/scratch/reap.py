import os
import signal

def reap():
    for p in os.listdir('/proc'):
        if p.isdigit() and p != '1':
            try:
                with open(f'/proc/{p}/cmdline', 'r', errors='ignore') as f:
                    cmd = f.read()
                if 'pytest' in cmd:
                    print(f"Killing pytest process {p}: {cmd[:50]}")
                    os.kill(int(p), signal.SIGKILL)
            except Exception:
                pass

if __name__ == '__main__':
    reap()
