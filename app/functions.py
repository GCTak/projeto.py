#encoding: utf-8
import os
import networkx as nx
import matplotlib.pyplot as plt
import contextily as ctx
import geopandas as gpd
from shapely.geometry import Point
from classes import Neighborhood, Node, Graph, Segment
import json
import heapq
import numpy as np

INVALID_OPTION = "Opção inválida"

def load_neighborhoods():
    try:
        # check if the file exists
        if os.path.exists('neighborhoods.json'):
            with open('neighborhoods.json', 'r') as file:
                neighborhoods_data = json.load(file)
                neighborhoods = []
                # the data is organized as Name, Coordinates (lat,lon), City
                for neighborhood in neighborhoods_data:
                    name = neighborhood["Name"]
                    coordinates = neighborhood["Coordinates"]
                    lat, long = coordinates.split(',')
                    city = neighborhood.get("City")  # Use get to safely access the key

                    neighborhood_obj = Neighborhood(name, float(lat), float(long), city)
                    neighborhoods.append(neighborhood_obj)
                    
            return neighborhoods
    except Exception as e:
        print(e)
        return False
    
    
def menu() -> int:
    print("")
    print("Menu")
    print("==========================================")
    print("1. Cadastrar bairro")
    print("2. Cadastrar segmento de rede")
    print("3. Visualizar grafo")
    print("4. Calcular menor caminho para novo segmento de rede")
    print("5. Gerar topologia de rede de custo minimo")
    print("6. Gerar matriz de adjacência")
    print("7. Gerar árvore geradora mínima")
    print("8. Carregar bairros de arquivo")
    print("9. Sair")
    print("")
    while True:
        try:
            option = int(input("--- Digite o número da opção escolhida: "))
            if option not in range(1, 10):
                print(INVALID_OPTION)
            else:
                return option
        except ValueError:
            print(INVALID_OPTION)

def register_neighborhood(number_of_neighborhoods: int) -> list:
    neighborhoods = []
    if number_of_neighborhoods <= 0 or not isinstance(number_of_neighborhoods, int):
        print("Número de bairros inválido.")
        return neighborhoods
        
    for _ in range(number_of_neighborhoods):
        name = input("Digite o nome do bairro: ")
        coordenada = input("Digite a latitude e longitude do bairro (separados por vírgula): ")
        latitude, longitude = map(float, coordenada.split(","))
        city = input("Digite a cidade do bairro: ")
        if city == "":
            neighborhoods.append(Neighborhood(name, latitude, longitude))
        else:
            neighborhoods.append(Neighborhood(name, latitude, longitude, city))
    return neighborhoods

def small_way(g, node_a, node_b):
    try:
        graph_nx = nx.Graph()
        for node in g.nodes:
            for neighbor, weight in node.adjacent_nodes.items():
                graph_nx.add_edge(node.neighborhood.name, neighbor.neighborhood.name, weight=weight)

        way = nx.dijkstra_path(graph_nx, node_a.neighborhood.name, node_b.neighborhood.name, weight='weight')
        cost = nx.dijkstra_path_length(graph_nx, node_a.neighborhood.name, node_b.neighborhood.name, weight='weight')
        return way, cost
    except nx.NetworkXNoPath:
        return None, float('inf')

def close_program():
    print("Programa encerrado.")
    exit()


def view_graph_on_map(g : Graph, is_mst=False):
    #O no do grafico deve ter o texto com o nome do bairro
    node_positions = {}
    for node in g.nodes:
        node_positions[node.neighborhood.name] = (node.neighborhood.longitude, node.neighborhood.latitude)
    
    node_gdf = gpd.GeoDataFrame(
        {'neighborhood': [node.neighborhood.name for node in g.nodes]},
        geometry=[Point(node.neighborhood.longitude, node.neighborhood.latitude) for node in g.nodes],
        crs="EPSG:4326"
    )

    _, ax = plt.subplots(figsize=(20, 20))
    if is_mst:
        ax.set_aspect('equal')

    # Plot nodes
    node_gdf.plot(ax=ax, color='blue')

    # Plot edges and add edge labels
    for node in g.nodes:
        for neighbor, weight in node.adjacent_nodes.items():
            x_values = [node.neighborhood.longitude, neighbor.neighborhood.longitude]
            y_values = [node.neighborhood.latitude, neighbor.neighborhood.latitude]
            ax.plot(x_values, y_values, color='black')
            mid_x = (x_values[0] + x_values[1]) / 2
            mid_y = (y_values[0] + y_values[1]) / 2
            ax.text(mid_x, mid_y, f'{weight:.2f}', color='red', fontsize=11, ha='center', va='center', bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'), zorder=5)

    # Plot node labels
    for node, position in node_positions.items():
        ax.text(position[0], position[1], node, fontsize=10, ha='center', va='center', bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'), zorder=5)

    # Add basemap
    ctx.add_basemap(ax, crs=node_gdf.crs.to_string(), source=ctx.providers.CartoDB.Positron)
    
    # Define aspect ratio of y-axis manually if aspect is not finite or positive
    if not np.isfinite(ax.get_aspect()):
        ax.set_aspect(1)
    
    plt.show()


def generate_minimum_spanning_tree(graph):
    """
    Gera uma árvore geradora mínima a partir de um grafo.
    """
    mst_graph = Graph()
    visited = set()
    heap = []
    start_node = graph.nodes[0]
    heapq.heappush(heap, (0, start_node, None))
    while heap:
        weight, node, parent = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        if parent:
            mst_graph.add_edge(parent, node, weight)
        for neighbor, w in node.adjacent_nodes.items():
            if neighbor not in visited:
                heapq.heappush(heap, (w, neighbor, node))
    return mst_graph

def view_mst_on_map(mst_graph):
    view_graph_on_map(mst_graph, is_mst=True)