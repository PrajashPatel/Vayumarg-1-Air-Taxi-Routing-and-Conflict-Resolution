from os import times
import osmnx as ox
import networkx as nx
from shapely.geometry import Point, Polygon
import matplotlib.pyplot as plt


# 1. GET CITY GRAPH
ox.settings.use_cache = True
ox.settings.log_console = True

center_point = (12.9716, 77.5946)

G = ox.graph_from_point(
    center_point,
    dist=3000,
    network_type="drive",
    simplify=False
)

print("Raw nodes:", len(G.nodes))

G = ox.simplify_graph(G)
print("After simplification:", len(G.nodes))

G = G.subgraph(
    max(nx.strongly_connected_components(G), key=len)
).copy()

print("Final nodes:", len(G.nodes))
print("Final edges:", len(G.edges))


# 2. NO-FLY ZONE (NFZ)

no_fly_zone = Polygon([
    (77.600, 12.975),
    (77.615, 12.975),
    (77.615, 12.990),
    (77.600, 12.990)
])

nodes_to_remove = []

for node, data in G.nodes(data=True):
    point = Point(data["x"], data["y"])
    if no_fly_zone.contains(point):
        nodes_to_remove.append(node)

print("Removing NFZ nodes:", len(nodes_to_remove))

G.remove_nodes_from(nodes_to_remove)

G = G.subgraph(
    max(nx.strongly_connected_components(G), key=len)
).copy()


# 3. DRONE SPEED & TRAVEL TIME

DRONE_SPEED = 15.0  # meters/sec

for u, v, k, data in G.edges(keys=True, data=True):
    length = data.get("length", 1)
    data["travel_time"] = length / DRONE_SPEED


# 4. BATTERY MODEL

MAX_FLIGHT_TIME = 30 * 60  # 1800 seconds 

def is_battery_feasible(battery_percent, required_time):
    max_possible_time = (battery_percent / 100.0) * MAX_FLIGHT_TIME
    return required_time <= max_possible_time


# 5. AIR TAXI CLASS

class AirTaxi:
    def __init__(self, taxi_id, start_lat, start_lon, dest_lat, dest_lon, battery):
        self.id = taxi_id
        self.start_lat = start_lat
        self.start_lon = start_lon
        self.dest_lat = dest_lat
        self.dest_lon = dest_lon
        self.battery = battery
        self.route = []
        self.arrival_times = {}
        self.total_time = 0.0
        self.delayed = False
        self.delay_time = 0.0
        self.altitude = 0  # meters, default ground level
        self.orig = None
        self.dest = None


# 6. MULTIPLE FLIGHT REQUESTS

flight_requests = [
    AirTaxi(1, 12.9750, 77.5900, 12.9600, 77.6200, 80),
    AirTaxi(2, 12.9750, 77.5900, 12.9600, 77.6200, 90),
    AirTaxi(3, 12.9650, 77.5850, 12.9700, 77.6300, 90),
    AirTaxi(6, 12.9700, 77.6000, 12.9600, 77.6300, 90),
    AirTaxi(7, 12.9550, 77.6150, 12.9750, 77.6000, 80),
    AirTaxi(8, 12.9650, 77.5800, 12.9650, 77.6400, 85),
    AirTaxi(9, 12.9600, 77.5800, 12.9600, 77.6400, 85)

]

accepted_taxis = []


# 7. ROUTE PLANNING & BATTERY CHECK

for taxi in flight_requests:

    print(f"\nProcessing Taxi {taxi.id}")

    orig = ox.distance.nearest_nodes(G, taxi.start_lon, taxi.start_lat)
    dest = ox.distance.nearest_nodes(G, taxi.dest_lon, taxi.dest_lat)

    try:
        route = nx.shortest_path(
            G,
            source=orig,
            target=dest,
            weight="travel_time"
        )
    except nx.NetworkXNoPath:
        print(f"❌ Taxi {taxi.id}: No path available (NFZ blockage)")
        continue

    # timeline
    arrival_times = {}
    current_time = 0.0
    arrival_times[orig] = current_time

    for u, v in zip(route[:-1], route[1:]):
        edge_data = min(
            G.get_edge_data(u, v).values(),
            key=lambda d: d["travel_time"]
        )
        current_time += edge_data["travel_time"]
        arrival_times[v] = current_time

    total_time = arrival_times[route[-1]]

    # 🔍 ADD THIS DEBUG PRINT
    print(
        f"Taxi {taxi.id} | "
        f"Route time = {total_time:.1f}s | "
        f"Battery allows = {(taxi.battery/100)*MAX_FLIGHT_TIME:.1f}s"
    )

    if not is_battery_feasible(taxi.battery, total_time):
        print(f"❌ Taxi {taxi.id} rejected (Battery insufficient)")
        continue

    # Accept the taxi
    taxi.route = route
    taxi.arrival_times = arrival_times
    taxi.total_time = total_time
    taxi.orig = orig
    taxi.dest = dest
    accepted_taxis.append(taxi)
    print(f"✅ Taxi {taxi.id} accepted")


# 8. CONFLICT DETECTION & CLASSIFICATION

conflicts = []

for i in range(len(accepted_taxis)):
    for j in range(i + 1, len(accepted_taxis)):
        taxi_a = accepted_taxis[i]
        taxi_b = accepted_taxis[j]

        # Classify conflict type
        shared_nodes = len(set(taxi_a.route) & set(taxi_b.route))
        total_unique = len(set(taxi_a.route) | set(taxi_b.route))
        shared_nodes_ratio = shared_nodes / total_unique if total_unique > 0 else 0

        if shared_nodes_ratio > 0.8:
            conflict_type = "SAME_PATH_CONFLICT"
        else:
            conflict_type = "CROSSING_PATH_CONFLICT"

        print(f"Detected {conflict_type} between Taxi {taxi_a.id} and {taxi_b.id}, shared_nodes={shared_nodes}, ratio={shared_nodes_ratio:.2f}")

        if conflict_type == "SAME_PATH_CONFLICT":
            # For same path, only add if time is close
            for node, time_a in taxi_a.arrival_times.items():
                if node in taxi_b.arrival_times:
                    time_b = taxi_b.arrival_times[node]
                    if abs(time_a - time_b) < 10.0:
                        conflicts.append({
                            "node": node,
                            "taxi_1": taxi_a.id,
                            "taxi_2": taxi_b.id,
                            "type": conflict_type
                        })
        elif conflict_type == "CROSSING_PATH_CONFLICT":
            # For crossing path, add once per pair, regardless of time (altitude solves potential conflicts)
            conflicts.append({
                "node": None,  # No specific node for crossing
                "taxi_1": taxi_a.id,
                "taxi_2": taxi_b.id,
                "type": conflict_type
            })


# 9. CONFLICT RESOLUTION (DELAY OR ALTITUDE)

DELAY_TIME = 30.0  # seconds

for conflict in conflicts:
    taxi_a = next(t for t in accepted_taxis if t.id == conflict["taxi_1"])
    taxi_b = next(t for t in accepted_taxis if t.id == conflict["taxi_2"])

    print(f"Resolving {conflict['type']} between Taxi {taxi_a.id} and {taxi_b.id} at node {conflict['node']}")

    if conflict["type"] == "SAME_PATH_CONFLICT":
        # Apply time delay
        delayed = taxi_a if taxi_a.battery < taxi_b.battery else taxi_b

        if delayed.delayed:
            continue   # already delayed once

        delayed.arrival_times = {
            node: time + DELAY_TIME
            for node, time in delayed.arrival_times.items()
        }
        delayed.total_time += DELAY_TIME
        delayed.delayed = True
        delayed.delay_time = DELAY_TIME

        if not is_battery_feasible(delayed.battery, delayed.total_time):
            print(f"⚠️ Taxi {delayed.id} became battery-infeasible after delay")

        print(f"⏱️ SAME_PATH_CONFLICT resolved: Taxi {delayed.id} delayed by {DELAY_TIME} seconds")

    elif conflict["type"] == "CROSSING_PATH_CONFLICT":
        # Apply altitude separation
        if taxi_a.altitude == 0 and taxi_b.altitude == 0:
            taxi_a.altitude = 100  # meters
            taxi_b.altitude = 150  # meters
            print(f" CROSSING_PATH_CONFLICT resolved: Taxi {taxi_a.id} at 100m, Taxi {taxi_b.id} at 150m")
        # If already assigned, skip
        else:
            print(f" CROSSING_PATH_CONFLICT already resolved for Taxi {taxi_a.id} and {taxi_b.id}")


#  FINAL SUMMARY

print("\n--- FINAL FLIGHT SUMMARY ---")
for taxi in accepted_taxis:
    status_parts = []
    if taxi.delayed:
        status_parts.append(f"DELAYED {taxi.delay_time}s")
    else:
        status_parts.append("ON TIME")

    if taxi.altitude > 0:
        status_parts.append(f"ALTITUDE {taxi.altitude}m")

    status = " | ".join(status_parts)

    print(
        f"Taxi {taxi.id} | {status} | "
        f"Total Time: {taxi.total_time:.1f}s"
    )


#  VISUALIZATION (SINGLE GRAPH)

# for taxi in accepted_taxis:
#     print(f"Plotting route for Taxi {taxi.id}")
#     ox.plot_graph_route(
#         G,
#         taxi.route,
#         route_color="red",
#         route_linewidth=3,
#         node_size=5
#     )

fig, ax = ox.plot_graph(
    G,
    node_size=3,
    edge_color="lightgray",
    show=False,
    close=False
)

colors = ["red", "blue", "green", "orange","purple", "brown", "pink", "gray", "olive", "cyan", "magenta"]

for i, taxi in enumerate(accepted_taxis):
    ox.plot_graph_route(
        G,
        taxi.route,
        route_color=colors[i % len(colors)],
        route_linewidth=3,
        node_size=0,
        ax=ax,
        show=False,
        close=False
    )

orig_x = []
orig_y = []

for taxi in accepted_taxis:
    n = taxi.orig
    orig_x.append(G.nodes[n]["x"])
    orig_y.append(G.nodes[n]["y"])

ax.scatter(
    orig_x,
    orig_y,
    c="green",
    s=40,
    marker="o",
    label="Origin",
    zorder=5
)

dest_x = []
dest_y = []

for taxi in accepted_taxis:
    n = taxi.dest
    dest_x.append(G.nodes[n]["x"])
    dest_y.append(G.nodes[n]["y"])

ax.scatter(
    dest_x,
    dest_y,
    c="red",
    s=40,
    marker="X",
    label="Destination",
    zorder=5
)
ax.legend()
plt.show()
