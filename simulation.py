import csv
from datetime import datetime, timedelta
import math
from engine.forecaster import DemandForecaster
from engine.staffing import StaffingManager
from engine.inventory import InventoryManager

def load_historical_data(forecaster: DemandForecaster, filename="data/historical_data.csv"):
    print("--- Phase 1: Loading Historical Data ---")
    try:
        with open(filename, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                forecaster.apply_feedback(
                    timestamp=row["timestamp"], 
                    actual=int(row["actual_covers"]), 
                    reason=row["reason"]
                )
        print("Historical training complete.\n")
    except FileNotFoundError:
        print(f"Could not find {filename}. Make sure your CSV is ready!")

def run_simulation():
    # Initialize Engines
    forecaster = DemandForecaster(storage_path="data/demand_state.json")
    staffing = StaffingManager(forecaster, storage_path="data/staffing_state.json")
    inventory = InventoryManager(forecaster, storage_path="data/inventory_state.json")

    # Train from history first
    load_historical_data(forecaster)

    print("--- Phase 2: The Learning Simulation (12 Weeks) ---\n")

    # 1. Base covers for Friday 19:00 = ~150
    # 2. True 'rain' multiplier = 0.8 (System starts at whatever history says, or 1.0)
    # 3. True 'festival' multiplier = 1.5 (System starts at whatever history says, or 1.0)
    # 4. True Chef capacity = 16 covers
    # 5. True Flour consumption = 0.12kg/cover

    error_tracker = {
        "normal": [],
        "rain": [],
        "festival": []
    }

    target_time = datetime(2026, 4, 10, 19, 0) # A Friday at 7 PM
    
    for week in range(1, 13):
        time_str = target_time.strftime("%Y-%m-%d %H:%M")
        
        # Schedule the events to test the coefficient learning
        if week in [3, 7, 11]:
            reason = "rain"
        elif week in [4, 8, 12]:
            reason = "festival"
        else:
            reason = "normal"

        print(f"=== WEEK {week} ({time_str}) | Condition: {reason.upper()} ===")

        # --- PREDICTION ---
        pred_covers = forecaster.predict(time_str, reason=reason)
        
        pred_staff = staffing.get_staff_requirements(time_str, reason=reason)["Kitchen"]["Chef"]
        pred_flour_order = inventory.get_order_prediction("flour", current_stock=0.0, current_time=target_time) 

        print(f"PREDICTED:")
        print(f"   - Covers (19:00): {pred_covers}")
        print(f"   - Chefs Scheduled (19:00): {pred_staff}")
        print(f"   - Weekly Flour Order: {pred_flour_order} kg")

        # --- REALITY ---
        # Base covers grow slightly over time (150 -> 162)
        true_base = 150 + week 
        
        if reason == "rain":
            actual_covers = int(true_base * 0.8)
        elif reason == "festival":
            actual_covers = int(true_base * 1.5)
        else:
            actual_covers = true_base
            
        # Add this right after you calculate actual_covers
        current_error = abs(actual_covers - pred_covers)
        error_tracker[reason].append(current_error)
            
        actual_flour_used = actual_covers * 0.12
        
        actual_chefs_needed = math.ceil(actual_covers / 16) 
        
        staff_diff = actual_chefs_needed - pred_staff

        print(f"ACTUAL RESULTS:")
        print(f"   - Covers (19:00): {actual_covers} (Error: {actual_covers - pred_covers})")
        print(f"   - Chefs Needed (19:00): {actual_chefs_needed} (Short by: {staff_diff})")
        print(f"   - Flour Used (19:00): {actual_flour_used:.1f} kg")

        # --- APPLY CONTINUOUS FEEDBACK ---
        print("Applying Feedback and Learning...")
        forecaster.apply_feedback(time_str, actual_covers, reason=reason)
        staffing.apply_feedback(actual_covers, actual_chefs_needed, "Kitchen", "Chef")
        inventory.apply_feedback("flour", actual_flour_used, actual_covers)

        # The updated coefficients to prove the system is learning
        current_rain = forecaster.impact_coefficients.get("rain", 1.0)
        current_fest = forecaster.impact_coefficients.get("festival", 1.0)
        print(f"Learned Coefficients -> Rain: {current_rain:.2f}x | Festival: {current_fest:.2f}x\n")

        # Move to next Friday
        target_time += timedelta(days=7)

    print("--- Simulation Complete ---")

    print("\n==================================================")
    print("      FINAL PERFORMANCE & LEARNING SUMMARY        ")
    print("==================================================")
    
    for condition, errors in error_tracker.items():
        if not errors: 
            continue
            
        initial_error = errors[0]
        final_error = errors[-1]
        improvement = initial_error - final_error
        
        print(f"Condition: {condition.upper()}")
        print(f"   - Initial Error : {initial_error} covers")
        print(f"   - Final Error   : {final_error} covers")
        
        if improvement > 0:
            print(f"   - Result        : Error shrank by {improvement} covers. Learning successful.")
        elif improvement < 0:
            print(f"   - Result        : Error grew by {abs(improvement)} covers. Needs tuning.")
        else:
            print(f"   - Result        : Error remained steady at {initial_error} covers.")
        print("-" * 50)

if __name__ == "__main__":
    run_simulation()