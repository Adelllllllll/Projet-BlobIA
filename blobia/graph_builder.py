import networkx as nx
import pandas as pd

def build_metro_graph(stations_df):
    """
    Construit un graphe où chaque station est un noeud et chaque voisin immédiat
    sur une ligne est relié par une arrête. Les correspondances sont créées là
    où plusieurs lignes partagent le même nom de station.
    """
    G = nx.Graph()

    # Ajouter tous les noeuds (stations)
    for idx, row in stations_df.iterrows():
        G.add_node(row['nom_so_gar'], **row.to_dict())
    
    # Relier chaque station à sa voisine immédiate sur chaque ligne
    lignes = stations_df['indice_lig'].unique()
    for ligne in lignes:
        stations_ligne = stations_df[stations_df['indice_lig'] == ligne]
        # Trie approximatif par latitude pour avoir une structure linéaire plausible
        stations_ligne = stations_ligne.sort_values(by=['Geo Point'])
        noms = stations_ligne['nom_so_gar'].tolist()
        for i in range(len(noms)-1):
            G.add_edge(noms[i], noms[i+1], line=ligne)

    # Création des correspondances : relie entre elles toutes les "versions" d'une même station sur plusieurs lignes
    station_group = stations_df.groupby('nom_so_gar')
    for nom, group in station_group:
        if len(group) > 1:
            # Si une station appartient à plusieurs lignes, on relie ces versions entre elles
            noms_lignes = group['indice_lig'].tolist()
            for i in range(len(noms_lignes)-1):
                G.add_edge(nom, nom, line='correspondance')

    return G
