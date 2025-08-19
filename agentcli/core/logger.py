"""Module for logging actions and creating diffs."""

import json
import os
from datetime import datetime


class Logger:
    
    def __init__(self, log_dir=".agentcli/logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        
    def log_action(self, action, description, details=None):

        log_id = datetime.now().strftime("%Y%m%d%H%M%S")
        log_entry = {
            "id": log_id,
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "description": description,
            "details": details or {}
        }
        
        log_path = os.path.join(self.log_dir, f"{log_id}.json")
        with open(log_path, 'w') as f:
            json.dump(log_entry, f, indent=2)
        
        return log_id
