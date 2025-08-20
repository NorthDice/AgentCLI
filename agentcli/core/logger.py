"""Module for logging actions and creating diffs."""

import json
import os
from datetime import datetime
import time


class Logger:
    
    def __init__(self, log_dir=".agentcli/logs"):
        self.log_dir = log_dir
        self._sequence_counter = 0
        os.makedirs(self.log_dir, exist_ok=True)
        
    def log_action(self, action, description, details=None):
        # Generate unique log ID using timestamp with microseconds and sequence counter
        now = datetime.now()
        timestamp_part = now.strftime("%Y%m%d%H%M%S")
        microseconds = now.microsecond
        
        # Increment sequence counter for actions within the same microsecond
        self._sequence_counter += 1
        
        log_id = f"{timestamp_part}{microseconds:06d}_{self._sequence_counter:03d}"
        
        log_entry = {
            "id": log_id,
            "timestamp": now.isoformat(),
            "action": action,
            "description": description,
            "details": details or {}
        }
        
        log_path = os.path.join(self.log_dir, f"{log_id}.json")
        with open(log_path, 'w') as f:
            json.dump(log_entry, f, indent=2)
        
        return log_id
