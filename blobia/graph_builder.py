import networkx as nx
import pandas as pd

def build_metro_graph(stations_df):
    """
    Construit un graphe où chaque station sur une ligne est un noeud (station|ligne),
    chaque voisin immédiat est relié par une arête, et les correspondances relient les 
    différentes versions (lignes) d’une même station physique.
    """
    G = nx.Graph()

    # Création des noeuds : station+ligne
    for idx, row in stations_df.iterrows():
        node_id = f"{row['nom_so_gar']}|{row['indice_lig']}"
        G.add_node(node_id, **row.to_dict())
        G.nodes[node_id]['Access'] = 1  # 1 = accessible, faute d'info réelle

    # Relier chaque station à sa voisine immédiate sur chaque ligne
    for ligne in stations_df['indice_lig'].unique():
        stations_ligne = stations_df[stations_df['indice_lig'] == ligne]
        stations_ligne = stations_ligne.sort_values(by=['Geo Point']) # approximation
        noms = stations_ligne['nom_so_gar'].tolist()
        node_ids = [f"{nom}|{ligne}" for nom in noms]
        for i in range(len(node_ids)-1):
            G.add_edge(node_ids[i], node_ids[i+1], line=ligne)

    # Création des correspondances interlignes (entre versions d'une même station physique)
    for nom, group in stations_df.groupby('nom_so_gar'):
        node_ids = [f"{row['nom_so_gar']}|{row['indice_lig']}" for idx, row in group.iterrows()]
        if len(node_ids) > 1:
            for i in range(len(node_ids)):
                for j in range(i+1, len(node_ids)):
                    G.add_edge(node_ids[i], node_ids[j], line='correspondance')

    return G
