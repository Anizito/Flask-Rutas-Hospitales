import csv
import heapq
import networkx as nx
import matplotlib.pyplot as plt
import math


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2 
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance

def load_coordinates(csv_file):
    coords = {}
    with open(csv_file, mode='r', encoding='utf-8-sig') as infile:  
        reader = csv.DictReader(infile, delimiter=';')
        
       
        print("Cabeceras del CSV:", reader.fieldnames)
        
        for row in reader:
            coords[row['id_eess']] = (float(row['latitud']), float(row['longitud']))
    return coords


def read_adj_list(file_path):
    adj_list = {}
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split(': ')
            node = parts[0]  
            neighbors = [tuple(neighbor.split('|')) for neighbor in parts[1].split(', ')]
            adj_list[node] = [(neighbor, float(weight)) for neighbor, weight in neighbors]
    return adj_list


def heuristic(node, goal, graph):
    lat1, lon1 = graph.nodes[node]['lat'], graph.nodes[node]['lon']
    lat2, lon2 = graph.nodes[goal]['lat'], graph.nodes[goal]['lon']
    return haversine(lat1, lon1, lat2, lon2)

def astar(graph, start, goal):
    visited = set()
    queue = [(0, start, 0, [])]  
    
    while queue:
        (priority, node, cost, path) = heapq.heappop(queue)
        
        if node in visited:
            continue
        
        path = path + [node]
        visited.add(node)
        
        if node == goal:
            return cost, path
        
       
        for neighbor in graph[node]:  
            if neighbor not in visited:
                weight = graph[node][neighbor]['weight']
                new_cost = cost + weight  
                priority = new_cost + heuristic(neighbor, goal, graph) 
                heapq.heappush(queue, (priority, neighbor, new_cost, path))
    
    return float("inf"), []  

def main():
    
    adj_list_file = "lista_adyacencia.txt"
    coords_file = "filtered_hospitals.csv"  
    adj_list = read_adj_list(adj_list_file)
    coords = load_coordinates(coords_file)  

    G = nx.Graph()

    for node, neighbors in adj_list.items():
        lat, lon = coords.get(node, (0, 0))  
        G.add_node(node, lat=lat, lon=lon)
        for neighbor, weight in neighbors:
            G.add_edge(node, neighbor, weight=weight)

    start_node = input("Ingrese el id_eess del hospital de inicio: ")
    goal_node = input("Ingrese el id_eess del hospital objetivo: ")

    cost, path = astar(G, start_node, goal_node) 

    if cost != float("inf"):
        print(f"Costo total: {cost:.6f}")
        print(f"Camino encontrado: {' -> '.join(path)}")
    else:
        print("No se pudo encontrar un camino entre los nodos proporcionados.")

    plt.figure(figsize=(8, 6))  
    pos = nx.spring_layout(G, k=20) 
    nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=100, font_size=10, font_weight='bold')
    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    plt.title("Grafo Completo")
    plt.show()  

    if path:
        subgraph = nx.DiGraph()  
        for i in range(len(path) - 1):
            subgraph.add_edge(path[i], path[i + 1], weight=G[path[i]][path[i + 1]]['weight'])

        plt.figure(figsize=(8, 6)) 
        nx.draw(subgraph, pos, with_labels=True, node_color='lightgreen', node_size=500, font_size=10, font_weight='bold', edge_color='red', width=2)
        subgraph_labels = nx.get_edge_attributes(subgraph, 'weight')
        nx.draw_networkx_edge_labels(subgraph, pos, edge_labels=subgraph_labels)
        plt.title("Camino Encontrado")
        plt.show()  

#main()
