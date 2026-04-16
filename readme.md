# Restaurant Resource Planning System 

This project is a lightweight, self-learning Restaurant Resource Planning System. It predicts how many customers will walk through the door, schedules the right amount of staff, and orders the exact amount of food needed to survive the week, all while continuously adjusting its own math based on real-world feedback. The system gets a little bit smarter after every feedback.

## How It Works: The "Self-Learning" Loop

Most forecasting systems rely on static averages. This system relies on a **Continuous Feedback Loop**. 

At the end of every shift, the system compares its *Predictions* to *Reality*. If it predicted we needed 4 chefs, but the manager had to call in 2 extra people, the system takes that "Error," applies a learning rate (`alpha`), and permanently adjusts its internal logic. Tomorrow, it will schedule smarter.

## The Three Core Engines

1. **Demand Forecaster (`forecaster.py`)**
   - Predicts hourly customer traffic ("covers").
   - Understands business hours and daily patterns.
   - Dynamically learns "Impact Coefficients" (e.g., automatically figuring out that rain drops traffic by 25%, but a local festival boosts it by 40%).

2. **Staffing Manager (`staffing.py`)**
   - Maps predicted customers to specific stations (Kitchen, Floor).
   - Learns the actual "Capacity" of the staff over time. If a new menu slows down the kitchen, the system will notice the drop in efficiency and start scheduling an extra chef.

3. **Inventory Manager (`inventory.py`)**
   - Looks ahead into the future to calculate exactly how much food is needed.
   - Respects order cycles and shelf-life (so it doesn't order 3 tons of flour at once).
   - Learns the true "Consumption Rate" of ingredients as recipes or portion sizes naturally change over time.

## Project Structure

```text
/restaurant-resource-planner
│
├── data/
│   ├── historical_data.csv       # 30-day baseline dataset
│   ├── demand_state.json         # Learned baselines & weather coefficients
│   ├── staffing_state.json       # Learned staff capacities
│   └── inventory_state.json      # Learned ingredient consumption rates
│
├── engine/
│   ├── __init__.py
│   ├── forecaster.py             # Core predictive math
│   ├── staffing.py               # Staff optimization
│   └── inventory.py              # Supply chain logic
│
└── simulator.py                  # The main execution script
```

## Run the Learning Simulation

Execute the main simulation which will train the model on the historical data, and then run the 12-week Friday night test to show the feedback loop in action.

`python simulator.py`
