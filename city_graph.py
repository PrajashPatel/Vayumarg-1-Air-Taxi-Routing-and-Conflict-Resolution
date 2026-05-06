from os import times
import osmnx as ox
import networkx as nx

# 1. Getting the city graph for a specified locaction
ox.settings.use_cache = True
ox.settings.log_console = True

center_point = (12.9716, 77.5946)

# Step 1: Download raw graph
G = ox.graph_from_point(
    center_point,
    dist=3000,
    network_type="drive",
    simplify=False
)

print("Raw nodes:", len(G.nodes))

# Step 2: Simplify
G = ox.simplify_graph(G)
print("After simplification:", len(G.nodes))

# Step 3: Keep largest strongly connected component
G = G.subgraph(
    max(nx.strongly_connected_components(G), key=len)
).copy()

print("Final nodes:", len(G.nodes))
print("Final edges:", len(G.edges))

# ox.plot_graph(G, node_size=5, edge_color='blue')


# Specifying the no flying Zones (NFZ) using polygons

from shapely.geometry import Point, Polygon

no_fly_zone = Polygon([
    (77.600, 12.975),
    (77.615, 12.975),
    (77.615, 12.990),
    (77.600, 12.990)
])

nodes_to_remove = []

for node, data in G.nodes(data=True):
    point = Point(data["x"], data["y"])  # lon, lat
    if no_fly_zone.contains(point):
        nodes_to_remove.append(node)

print("Removing nodes:", len(nodes_to_remove))

G.remove_nodes_from(nodes_to_remove)


G = G.subgraph(
    max(nx.strongly_connected_components(G), key=len)
).copy()

#ox.plot_graph(G, node_size=5, edge_color='green')
 

# 2. Deciding the speed, time, and other constraints
DRONE_SPEED = 15.0  # meters per second

for u, v, k, data in G.edges(keys=True, data=True):
    length = data.get("length", 1)
    data["travel_time"] = length / DRONE_SPEED

#  Define Start & Destination (Snap to Graph)
# Example user input (lat, lon)
start_lat, start_lon = 12.9750, 77.5900
dest_lat, dest_lon   = 12.9600, 77.6200

orig = ox.distance.nearest_nodes(G, start_lon, start_lat)
dest = ox.distance.nearest_nodes(G, dest_lon, dest_lat)

print("Start node:", orig)
print("Destination node:", dest)

# finding the optimised or shortest route base on travel time
route = nx.shortest_path( # This is Dijkstra’s algorithm, Because you used weight=travel_time
    G,
    source=orig,
    target=dest,
    weight="travel_time"
)

print("Route length (nodes):", len(route))

#UAM needs to know: WHEN the drone is at each point  
# Not just WHERE  This code converts: path + edge times → timeline

arrival_times = {}
current_time = 0.0  # seconds : the current departure time

MAX_FLIGHT_TIME = 30 * 60   # 30 minutes = 1800 seconds (assumption)


arrival_times[orig] = current_time

for u, v in zip(route[:-1], route[1:]):
    edge_data = min(
        G.get_edge_data(u, v).values(),
        key=lambda d: d["travel_time"]
    )
    current_time += edge_data["travel_time"]
    arrival_times[v] = current_time

total_time = arrival_times[route[-1]]

def is_battery_feasible(battery_percent, required_time):
    max_possible_time = (battery_percent / 100.0) * MAX_FLIGHT_TIME
    return required_time <= max_possible_time
battery = 60  # example user input

if not is_battery_feasible(battery, total_time):
    print("❌ Flight rejected: insufficient battery")

else:
    print(f"Total flight time: {total_time:.2f} seconds")
    print(f"Total flight time: {total_time/60:.2f} minutes")
   
    ox.plot_graph_route(
        G,
        route,
        route_color="red",
        route_linewidth=3,
        node_size=5
    )




# for taxi in accepted_taxis:
#     print(f"Plotting route for Taxi {taxi.id}")
#     ox.plot_graph_route(
#         G,
#         taxi.route,
#         route_color="red",
#         route_linewidth=3,
#         node_size=5
#     )