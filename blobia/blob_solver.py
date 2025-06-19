import networkx as nx
import numpy as np

def get_affluence(station, affluence_df, jour, heure):
    """Retourne l’affluence de la station à la bonne heure/jour."""
    subset = affluence_df[
        (affluence_df['Station la plus proche'] == station)
        & (affluence_df['Jour'] == jour)
        & (affluence_df['Heure'] == heure)
    ]
    if subset.empty:
        return 1.0  # Valeur par défaut si pas d'info
    aff = subset.iloc[0]['Affluence']
    return aff if not np.isnan(aff) else 1.0

def blob_solver(graph, start_station, end_station, affluence_df, jour, heure, 
                alpha=0.5, beta=0.5, accessible_only=False):
    """
    Trouve le chemin optimal entre start_station et end_station selon une logique blob.
    """
    # Pondération sur chaque arrête :
    for u, v, data in graph.edges(data=True):
        afflu_u = get_affluence(u, affluence_df, jour, heure)
        afflu_v = get_affluence(v, affluence_df, jour, heure)
        afflu_moy = (afflu_u + afflu_v) / 2
        temps = 1.0  # Pas de vraie donnée de temps pour l’instant

        # Gérer accessibilité
        access_u = data.get('Access', 1)
        access_v = data.get('Access', 1)
        if accessible_only and (not access_u or not access_v):
            weight = float('inf')
        else:
            weight = alpha * temps + beta * afflu_moy
        graph[u][v]['weight'] = weight

    # Trouver le plus court chemin selon le poids
    try:
        path = nx.shortest_path(graph, start_station, end_station, weight='weight')
        total_weight = sum(graph[u][v]['weight'] for u, v in zip(path[:-1], path[1:]))
        return path, total_weight
    except nx.NetworkXNoPath:
        return [], float('inf')
