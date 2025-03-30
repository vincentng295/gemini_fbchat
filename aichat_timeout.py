import subprocess
import threading
import calc
import sys

def run_with_timeout(cmd, timeout_sec):
    """Run a command with a timeout on Windows."""
    try:
        # Start the main process
        proc = subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        
        # Schedule bridge_workflows.py to run after (timeout_sec - 120) seconds
        def run_bridge():
            print("Launching bridge_workflows.py...")
            subprocess.Popen("python bridge_workflows.py", shell=True)

        bridge_timer = threading.Timer(timeout_sec - 120, run_bridge)
        bridge_timer.daemon = True
        bridge_timer.start()

        # Wait for the main process to complete or timeout
        proc.communicate(timeout=timeout_sec)

    except subprocess.TimeoutExpired:
        # Timeout occurred. Notify and write to exitnow.txt
        print(f"Process timed out after {timeout_sec} seconds. Terminating...")
        try:
            with open("exitnow.txt", "w") as file:
                file.write("1")  # Tell aichat.py to stop by itself
        except Exception:
            pass

        try:
            print("Waiting for the process to terminate gracefully...")
            proc.communicate(timeout=600)
            print("Process terminated gracefully within 10 minutes.")
        except subprocess.TimeoutExpired:
            print("Forcefully killing the process.")
            proc.terminate()
            proc.communicate()
    except Exception as e:
        print(f"An error occurred: {e}")
        proc.terminate()
        proc.communicate()
    exit()

# Example usage:
command = "python aichat.py"

if __name__ == "__main__" and len(sys.argv) >= 2:
    timeout_seconds = int(sys.argv[1])
else:
    timeout_seconds = calc.to_sec(5, 30, 0)
print("Run with limited time:", timeout_seconds)
run_with_timeout(command, timeout_seconds)
