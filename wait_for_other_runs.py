import os
import time
import sys
from github_utils import no_other_workflows_running, get_workflow_id

sys.stdout.reconfigure(encoding='utf-8')

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
WORKFLOW_ID = os.getenv("WORKFLOW_ID")
CURRENT_RUN_ID = os.getenv("CURRENT_RUN_ID")

# Check if the GITHUB_REPO is not None or an empty string
if GITHUB_REPO is not None and GITHUB_REPO != "":
    print("Đang đợi các GitHub workflows khác hoàn thành...")
    workflow_id, _msg = get_workflow_id(GITHUB_TOKEN, GITHUB_REPO, WORKFLOW_ID), None
    # Loop until no other workflows are running
    while True:
        result, msg = no_other_workflows_running(GITHUB_TOKEN, GITHUB_REPO, workflow_id, CURRENT_RUN_ID)
        if result == True:
            break
        if _msg != msg:
            print(msg)
            _msg = msg
        time.sleep(5)
    print("Không có GitHub workflows nào đang chạy")