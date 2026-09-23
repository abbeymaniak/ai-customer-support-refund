"""Policy service for loading and evaluating the machine-readable refund policy."""

import json
from pathlib import Path
from typing import Any


class PolicyService:
    def __init__(self, policy_path: str = "data/refund_policy.json"):
        self.policy_path = Path(policy_path)
        self._policy: dict[str, Any] = {}

    def load_policy(self) -> dict[str, Any]:
        """Load refund policy JSON from disk."""
        if not self.policy_path.exists():
            return {}
        with open(self.policy_path, encoding="utf-8") as f:
            self._policy = json.load(f)
        return self._policy

    def get_policy(self) -> dict[str, Any]:
        """Return the loaded policy or load if needed."""
        if not self._policy:
            return self.load_policy()
        return self._policy
