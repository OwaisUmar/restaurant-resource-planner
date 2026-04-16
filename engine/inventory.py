from datetime import datetime, timedelta
import json
import math
import os

from engine.forecaster import DemandForecaster

class InventoryManager:
    def __init__(self, forecaster: DemandForecaster, storage_path: str = "inventory_state.json") -> None:
        self.forecaster = forecaster
        self.storage_path = storage_path
        self.ingredients_state = self._load_state() 
        self.alpha = 0.1

    def _load_state(self) -> dict:
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                return data
        return {}
    
    def _save_state(self) -> None:
        with open(self.storage_path, 'w') as f:
            json.dump(self.ingredients_state, f, indent=4)
    
    def get_predicted_covers(self, start: datetime, end: datetime) -> int:
        """Returns total predicted covers for a given window excluding close hours"""
        total_covers = 0
        open_hours = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
        curr = start

        while curr < end:
            if curr.hour in open_hours:
                total_covers += self.forecaster.predict(curr.strftime("%Y-%m-%d %H:%M"))
            curr += timedelta(hours=1)

        return total_covers
    
    def get_order_prediction(self, ingredient_id: str, current_stock: float, current_time: datetime | None = None) -> int:
        """Returns stock order size for given ingredient id on cover predictions in a future window based on lead time & shelf time."""
        
        if not current_time:
            current_time = datetime.now()
        
        ingredient = self.ingredients_state[ingredient_id]

        # Future window based on lead_time & shelf_life
        delivery_date = current_time + timedelta(days=ingredient["lead_time"])
        expiry_date = delivery_date + timedelta(days=min(7, ingredient["shelf_life"]))
        
        # Total covers predicted from self.forecaster for that window
        total_predicted_covers = self.get_predicted_covers(delivery_date, expiry_date)
        
        # Target stock
        target_stock = (total_predicted_covers * ingredient["consumption_rate"]) * ingredient["safety_buffer"]
        return math.ceil(max(0, target_stock - current_stock))

    def apply_feedback(self, ingredient_id: str, actual_usage: float, actual_covers: int) -> None:
        """Self-learns and updates the consumption rate coefficient from the feedback loop"""
        
        # Error based on actual consumption rate and learned consumption rate
        actual_consumtion_rate = actual_usage / actual_covers if actual_covers > 0 else 0
        learned_consumption_rate = self.ingredients_state[ingredient_id]["consumption_rate"]
        error = actual_consumtion_rate - learned_consumption_rate
        
        # Update the consumption_rate coefficient
        self.ingredients_state[ingredient_id]["consumption_rate"] += (self.alpha * error)
        
        self._save_state()