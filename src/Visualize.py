import matplotlib.pyplot as plt
import networkx as nx
import pickle

with open('graph.pkl', 'rb') as file:
    travel_times = pickle.load(file)
G = nx.DiGraph()
for start_location, destinations in travel_times.items():
    for end_location, time in destinations.items():
        G.add_edge(start_location, end_location, weight=time)
pos = nx.spring_layout(G, k=0.15, iterations=20)
nx.draw(G, pos, with_labels=False, node_size=700, node_color='skyblue', arrowsize=20)
location_to_index = {location: i for i, location in enumerate(G.nodes())}
index_to_location = {i: location for i, location in enumerate(G.nodes())}
for location, index in location_to_index.items():
    x, y = pos[location]
    plt.text(x, y, s=index, horizontalalignment='center', verticalalignment='center', 
             fontsize=8, bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.5'))
plt.axis('off')
plt.show()