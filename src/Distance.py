import os
import requests
import heapq
import pickle
from geopy.distance import geodesic
import folium
from folium import plugins
import json

api_key = 'b2c6ba02-2a88-471b-a596-aaa35e320252'
coordinates = [(35.54939, 139.77983), (35.65905, 139.70062), (35.71006, 139.8107),
               (35.65858, 139.74543), (35.71476, 139.79665), (35.66532, 139.77088),
               (35.68517, 139.75279), (35.72013, 139.76076), (35.67136, 139.76573),
               (35.67089, 139.7077), (35.71475, 139.77343), (35.70563, 139.75189),
               (35.65948, 139.70055), (35.69049, 139.74637), (35.63656, 139.76314),
               (35.69413, 139.74384), (35.68123, 139.76712)]

locations_name = ["Haneda Airport", "Hachikō Memorial Statue", "Tokyo Skytree",
                   "Tokyo Tower", "Sensō-ji", "Tsukiji Outer Market",
                   "Imperial Palace", "Nezu Shrine", "Art Aquarium museum",
                   "Harajuku Street", "Ueno Park", "Tokyo Dome",
                   "Shibuya Scramble Crossing", "Chidorigafuchi Moat",
                   "Rainbow Bridge", "Yasukuni Jinja", "Tokyo Station"]

graph_file_path = 'graph.pkl'
def initialize_or_load_graph(coordinates, locations_name, api_key, graph_file_path):
    if os.path.exists(graph_file_path):
        with open(graph_file_path, 'rb') as file:
            graph = pickle.load(file)
    else:
        graph = {}
        for i in range(len(coordinates)):
            for j in range(i + 1, len(coordinates)):
                node1, node2 = locations_name[i], locations_name[j]
                coord1, coord2 = coordinates[i], coordinates[j]
                travel_time = get_travel_time(coord1, coord2)
                if node1 not in graph:
                    graph[node1] = {}
                if node2 not in graph:
                    graph[node2] = {}
                graph[node1][node2] = travel_time
                graph[node2][node1] = travel_time
        with open(graph_file_path, 'wb') as file:
            pickle.dump(graph, file)
    return graph

def get_travel_time(coord1, coord2):
    endpoint = f'https://graphhopper.com/api/1/route?point={coord1[0]},{coord1[1]}&point={coord2[0]},{coord2[1]}&vehicle=car&key={api_key}'
    response = requests.get(endpoint)
    data = response.json()
    if 'paths' in data and len(data['paths']) > 0:
        travel_time_milliseconds = data['paths'][0]['time']
        travel_time_hours = travel_time_milliseconds/3600000
        with open('tex.json', 'a') as json_file:
            json_file.seek(0, 2)
            if json_file.tell() > 0:
                json_file.write(',')
            json.dump(data, json_file, indent=2)
            json_file.write('\n')
        return travel_time_hours
    else:
        print(f'Error retrieving travel duration from {coord1} to {coord2}')
        return float('inf')

def travel_time_heuristic(node1, node2, graph):
    heuristic_factor = 0.5  
    if node1 in graph and node2 in graph[node1]:
        return graph[node1][node2] * heuristic_factor
    else:
        return 0    


def a_star(graph, start, end, heuristic, visited):
    open_set = []
    heapq.heappush(open_set, (0, start, [start], 0))
    while open_set:
        _, current_node, path, current_time = heapq.heappop(open_set)
        if current_node == end:
            return path, current_time
        for neighbor, time in graph[current_node].items():
            if neighbor not in visited: 
                new_time = current_time + time
                estimated_total_time = new_time + heuristic(neighbor, end)
                heapq.heappush(open_set, (estimated_total_time, neighbor, path + [neighbor], new_time))

    return None, float('inf')

def find_route(graph, start, end=None):
    unvisited = set(locations_name)
    unvisited.remove(start)
    if end and end in unvisited:
        unvisited.remove(end)
    visited = set()  
    current_node = start
    end_node = end
    total_route = [start]   
    total_time = 0
    while unvisited:
        next_node = min(unvisited, key=lambda node: travel_time_heuristic(node, current_node, graph))
        unvisited.remove(next_node)
        path, time = a_star(graph, current_node, next_node, lambda x, y: travel_time_heuristic(x, y, graph), visited)
        total_route.extend(path[1:])
        total_time += time
        current_node = next_node
        visited.update(path)
    if end:
        final_path, final_time = a_star(graph, current_node, end, lambda x, y: 0, visited)
    else:
        final_path, final_time = [], 0  

    if final_path:
        total_route.extend(final_path[1:])
        total_time += final_time

    return total_route, total_time

def display_route_on_map(route, coordinates, locations_name):
    map_center = coordinates[locations_name.index(route[0])]
    my_map = folium.Map(location=map_center, zoom_start=13)
    route_coords = []
    for i, location in enumerate(route):
        index = locations_name.index(location)
        coord = coordinates[index]
        route_coords.append(coord)
        if i == 0 :
            marker_color = 'red'
        elif i == len(route) - 1:
            marker_color = 'green'
        else:
            marker_color = 'blue'
        popup_text = f"{i + 1}. {location}"
        folium.Marker(
            location=coord, 
            popup=popup_text, 
            icon=folium.Icon(color=marker_color)
        ).add_to(my_map)
    plugins.AntPath(locations=route_coords, color='blue', weight=5, delay=1000).add_to(my_map)
    my_map.save('route_map.html')
    import webbrowser
    webbrowser.open('route_map.html', new=2)

def print_route(route):
    print("Route:")
    for i in range(len(route) - 1):
        print(f"[{route[i]}] ->", end=' ')
    print(f"[{route[-1]}]")

graph = initialize_or_load_graph(coordinates, locations_name, api_key, graph_file_path)
tokyo_station_response = input("Do you want to make Tokyo Station the final destination or a stop on the route? Enter 'final' for final destination or 'stop' for a stop on the route: ")
if tokyo_station_response.lower() == 'final':
    route, time = find_route(graph, "Haneda Airport", end="Tokyo Station")
    print_route(route)
    print("Total Time (hours):", time)  
elif tokyo_station_response.lower() == 'stop':
    route, time = find_route(graph, "Haneda Airport")
    if "Tokyo Station" not in route:
        print("Please make sure to have tokyo inside the list of destination!")
    else:
        print_route(route)
        print("Total Time (hours):", time) 
else:
    print("Invalid input. Please enter 'final' or 'stop'.")

while True:
    map_response = input("Do you want to display the route map? (yes/no): ")
    
    if map_response.lower() == 'yes':
        display_route_on_map(route, coordinates, locations_name)
        break
    elif map_response.lower() == 'no':
        break
    else:
        print("Invalid input. Please enter 'yes' or 'no'.")

