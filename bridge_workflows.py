from github_utils import bridge_workflows
import os

PAT = os.getenv("PAT", "")
if PAT:
    bridge_workflows(PAT, False)