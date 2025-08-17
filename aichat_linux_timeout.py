import subprocess
import threading
import calc
import sys
import os
import signal

def run_with_timeout(cmd, timeout_sec):
    """Run a command with a timeout on Linux."""

    def sigint_handler(signum, frame):
        print("Ctrl+C detected. Sending SIGINT to child process group...")
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGINT)
        except Exception:
            pass

    signal.signal(signal.SIGINT, sigint_handler)

    try:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            preexec_fn=os.setsid
        )

        def run_bridge():
            print("Launching bridge_workflows.py...")
            subprocess.Popen("python3 bridge_workflows.py", shell=True)

        bridge_timer = threading.Timer(timeout_sec - 120, run_bridge)
        bridge_timer.daemon = True
        bridge_timer.start()

        proc.communicate(timeout=timeout_sec)

    except subprocess.TimeoutExpired:
        print(f"Process timed out after {timeout_sec} seconds. Terminating...")
        try:
            with open("exitnow.txt", "w") as file:
                file.write("1")
        except Exception:
            pass

        try:
            print("Waiting for the process to terminate gracefully...")
            proc.communicate(timeout=600)
            print("Process terminated gracefully within 10 minutes.")
        except subprocess.TimeoutExpired:
            print("Forcefully killing the process group.")
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except Exception:
                proc.terminate()
            proc.communicate()
    except Exception as e:
        print(f"An error occurred: {e}")
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            proc.terminate()
        proc.communicate()
    exit()

# Example usage:
command = "python3 aichat.py"

if __name__ == "__main__" and len(sys.argv) >= 2:
    timeout_seconds = int(sys.argv[1])
else:
    timeout_seconds = calc.to_sec(5, 30, 0)

print("Run with limited time:", timeout_seconds)
run_with_timeout(command, timeout_seconds)
