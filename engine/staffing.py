import json
import math
import os

from engine.forecaster import DemandForecaster

class StaffingManager:
    def __init__(self, forecaster: DemandForecaster, storage_path: str = "staffing_state.json") -> None:
        self.forecaster = forecaster
        self.storage_path = storage_path
        self.alpha = 0.1
        self.staff_state = self._load_state() 

    def _load_state(self) -> dict:
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                return data
        return {}
    
    def _save_state(self) -> None:
        with open(self.storage_path, 'w') as f:
            json.dump(self.staff_state, f, indent=4)

    def get_staff_requirements(self, timestamp: str, reason: str | None = None) -> dict:
        """Returns staff requirements for given timestamp based on predicted covers"""
        
        # Get predcited covers for this hour
        pred_covers = self.forecaster.predict(timestamp, reason=reason)
        
        requirements = {}
        for station, roles in self.staff_state.items():
            requirements[station] = {}
            for role, stats in roles.items():
                role_count = math.ceil(pred_covers / stats["capacity"])
                requirements[station][role] = max(role_count, stats["min"]) if pred_covers > 0 else 0
                
        return requirements

    def apply_feedback(self, actual_covers: int, actual_staff: int, station: str, role: str) -> None:
        """Learns the true capacity of a role based on real-world performance."""
        
        if station not in self.staff_state or role not in self.staff_state[station]:
            return
        if actual_staff <= 0 or actual_covers <= 0:
            return
        
        curr_capacity = self.staff_state[station][role]["capacity"]
        actual_capacity = actual_covers / actual_staff

        error = actual_capacity - curr_capacity
        self.staff_state[station][role]["capacity"] += (self.alpha * error)
        
        self._save_state()