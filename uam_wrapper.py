# uam_wrapper.py
import pandas as pd
from simulation import run_iterations, load_distance_map, initialize_plane_status_loc
from initialization import initialize_states_with_time
from metrics import calculate_cost

def run_uam_optimization(fleet_size, ticket_price, battery_range, time_steps,
                         charging_rate, discharge_rate, speed, min_route_distance):
    """
    Wrapper to run your simulation pipeline using dynamic vertiport locations
    from 'adjusted_vertiports_numeric.csv', and pass them to run_iterations.
    
    Parameters:
      fleet_size (int): Number of vehicles per vertiport.
      ticket_price (float): Cost per km for the flight.
      battery_range (float): eVTOL battery capacity in km (if used).
      time_steps (int): Number of simulation iterations to run.
      charging_rate (float): Fraction of full battery recharged per time step (e.g., 0.5 -> 50%).
      discharge_rate (float): Battery consumption per km.
      speed (float): eVTOL cruising speed in km/h.
      min_route_distance (float): Minimum distance (km) for a valid trip.
      
    Returns:
      (coverage_rate, total_cost, demand_served) - key performance metrics.
    """
    # 1) Load dynamic vertiport locations from your K-means CSV
    vertiports_df = pd.read_csv("adjusted_vertiports_numeric.csv")
    vertiports = vertiports_df["Vertiport"].tolist()
    
    # 2) Load distance matrix for your simulation
    distance_map = load_distance_map("distance_matrix.csv")
    
    # 3) Create vehicles
    vehicles = [f"V{i}" for i in range(1, fleet_size * len(vertiports) + 1)]
    
    # 4) Initialize states
    vehicle_states, vertiport_states = initialize_states_with_time(vehicles, vertiports, fleet_size)
    
    # 5) Initialize plane status
    plane_status = initialize_plane_status_loc(vehicles, vertiports, fleet_size)
    
    # 6) Activate all vertiports (if your logic requires it)
    for v in vertiports:
        vertiport_states[v]["activated"] = True
    
    # 7) Prepare an empty gurobi_results_per_time list for each iteration
    #    (If your pipeline loads actual results, you can do so here instead.)
    gurobi_results_per_time = [[] for _ in range(time_steps)]
    
    # 8) Run the simulation
    #    NOTE: We add a new parameter `vertiports=vertiports` in run_iterations
    total_met_demand, total_demand = run_iterations(
        num_iterations=time_steps,
        vehicle_states=vehicle_states,
        vertiport_states=vertiport_states,
        gurobi_results_per_time=gurobi_results_per_time,
        charging_rate=charging_rate,
        discharge_rate=discharge_rate,
        regenerate_solution=None,   # or your actual function
        plane_status=plane_status,
        distance_map=distance_map,
        vertiports=vertiports      # <--- pass vertiports here
    )
    
    coverage_rate = total_met_demand / total_demand if total_demand else 0
    
    # 9) Calculate cost using your cost function
    #    If you have real Gurobi results, pass them here. This is just a placeholder.
    gurobi_results = []
    total_cost = calculate_cost(
        flow_data=gurobi_results,
        cost_per_distance=ticket_price,
        distance_map=distance_map
    )
    
    return coverage_rate, total_cost, total_met_demand

# Quick test if running directly
if __name__ == "__main__":
    cov, cost, served = run_uam_optimization(
        fleet_size=20,
        ticket_price=4.0,
        battery_range=100,
        time_steps=5,
        charging_rate=0.5,
        discharge_rate=0.1,
        speed=150,
        min_route_distance=20
    )
    print(f"Coverage Rate: {cov}\nTotal Cost: {cost}\nDemand Served: {served}")
