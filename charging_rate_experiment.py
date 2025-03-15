# charging_rate_experiment.py
from uam_wrapper import run_uam_optimization

# Fixed parameters (based on your project defaults)
fleet_size     = 20          # vehicles per vertiport
ticket_price   = 4.0         # $/km
battery_range  = 100         # km
time_steps     = 10          # simulation iterations per run
discharge_rate = 0.1         # fixed discharge rate (per km)
speed          = 150         # km/h (fixed)
min_route_dist = 20          # km (fixed)

# Charging rate range: 0.30 to 0.70 (i.e., 30% to 70%)
charging_rates = [0.30, 0.40, 0.50, 0.60, 0.70]

# Number of simulation runs per parameter value
num_runs = 10

# Open a CSV file to save all results (or you can save one file per parameter value)
output_filename = "charging_rate_experiment_results.csv"
with open(output_filename, "w") as out_file:
    # Write header
    out_file.write("Charging Rate,Run Number,Coverage Rate,Total Cost,Demand Served\n")
    
    # Loop over each charging rate value
    for rate in charging_rates:
        for run in range(1, num_runs + 1):
            # Run the simulation with the given charging rate
            coverage_rate, total_cost, demand_served = run_uam_optimization(
                fleet_size=fleet_size,
                ticket_price=ticket_price,
                battery_range=battery_range,
                time_steps=time_steps,
                charging_rate=rate,
                discharge_rate=discharge_rate,
                speed=speed,
                min_route_distance=min_route_dist
            )
            # Write results for this run into the CSV file
            out_file.write(f"{rate},{run},{coverage_rate},{total_cost},{demand_served}\n")
            # print(f"Finished run {run} for charging rate {rate}.")
            
print(f"All results saved to {output_filename}.")
