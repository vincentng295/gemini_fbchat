from github_utils import bridge_workflows
import os

PAT = os.getenv("PAT", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "") 
try: 
    bridge_workflows(PAT if PAT else GITHUB_TOKEN, False)
except Exception:
    bridge_workflows(GITHUB_TOKEN, False)