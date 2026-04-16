from datetime import datetime
import json
import os

class DemandForecaster:
    def __init__(self, storage_path: str = "demand_state.json") -> None:
        self.storage_path = storage_path
        state = self._load_state()
        self.estimates = {self._decode_key(k): v for k, v in state["estimates"].items()}
        self.impact_coefficients = state["impact_coefficients"]
        self.alpha = 0.2
        
    def _encode_key(self, day: int, hour: int) -> str:
        """Util function to encode a pair of day and hour, since JSON does not support tuples dict keys."""
        return f"{day}_{hour}"
        
    def _decode_key(self, key: str) -> tuple:
        """Util function to decode a key to tuple of day and hour."""
        return tuple(map(int, key.split("_")))
        
    def _load_state(self) -> dict:
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                return data
        return {}

    def _save_state(self) -> None:
        with open(self.storage_path, 'w') as f:
            json.dump({
                "metadata": {"alpha": self.alpha, "last_updated": str(datetime.now())},
                "estimates": {self._encode_key(k[0], k[1]): round(v, 2) for k, v in self.estimates.items()},
                "impact_coefficients": {k: round(v, 2) for k, v in self.impact_coefficients.items()}
            }, f, indent=4)
        
    def apply_feedback(self, timestamp: str, actual: int, reason: str | None = None) -> None:
        """Compares the predicted customers against reality and continuously adjusts the system's internal math so the next prediction is more accurate."""
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
        key = (dt.weekday(), dt.hour)
        
        # Calculate prediction with current coefficients
        pred = self.predict(timestamp)
        coeff = self.impact_coefficients.get(reason, 1.0)
        coeff_pred = pred * coeff
        
        error = actual - coeff_pred
        
        if key not in self.estimates:
                self.estimates[key] = float(actual)
        
        if reason and reason in self.impact_coefficients:
            # Learn and update coefficient, not estimates
            ideal_coeff = actual / pred if pred > 0 else 1.0
            self.impact_coefficients[reason] += self.alpha * (ideal_coeff - coeff)
        else:
            # Learn and update estimates for a normal day    
            self.estimates[key] += self.alpha * error
                
        self._save_state()
        
    def predict(self, timestamp: str, reason: str | None = None) -> int:
        """Predicts expected customer traffic by applying learned coefficients (like rain or festivals) to the historical baseline for that specific hour."""
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
        key = (dt.weekday(), dt.hour)
        
        # Default covers to start with
        base_covers = 30
        
        # Lookup in estimates for learned value from feedback
        if key in self.estimates:
            base_covers = round(self.estimates[key])
        
        coeff = self.impact_coefficients.get(reason, 1.0)
        return round(base_covers * coeff)