import networkx as nx
import numpy as np
import pandas as pd
from collections import defaultdict


def get_affluence(station_name, line_id, affluence_df, jour, heure, reduction_coeff=0.7):
    """Retourne l’affluence d'une station à la bonne heure/jour.
       Si absente, prend la station la plus proche sur la même ligne avec une pénalité."""

    # ADAPTE CES NOMS DE COLONNES ICI !
    subset = affluence_df[
        (affluence_df['Nom station'] == station_name)     # <-- adapte ici !
        & (affluence_df['Ligne'] == line_id)
        & (affluence_df['Jour'] == jour)
        & (affluence_df['Heure'] == heure)
    ]
    if not subset.empty:
        aff = subset.iloc[0]['Affluence']
        return aff if not pd.isna(aff) else 1.0

    # Sinon, cherche une station voisine sur la même ligne
    same_line = affluence_df[
        (affluence_df['Ligne'] == line_id)
        & (affluence_df['Jour'] == jour)
        & (affluence_df['Heure'] == heure)
    ]
    if not same_line.empty:
        closest_aff = same_line['Affluence'].min()
        return reduction_coeff * closest_aff
    return 1.0  # valeur par défaut si aucune info


def blob_solver_bioinspire(graph, start_station, end_station, affluence_df, jour, heure,
                           alpha=0.5, beta=0.5, accessible_only=False, n_iter=1500, flux_init=1000000, evaporation=0, verbose=True):
    """
    Algorithme bio-inspiré façon blob : exploration multi-chemins par propagation de flux.
    - À chaque itération, le flux se propage vers les voisins (pondéré par la qualité des arêtes)
    - Les arêtes traversées accumulent un renforcement (plus il y a de flux, plus la trace est forte)
    - On extrait le chemin ayant reçu le plus de flux à l'arrivée
    - Log de tous les flux pour visualiser l’exploration “blob”
    """
    G = graph.copy()
    for u, v, data in G.edges(data=True):
        nom_u = G.nodes[u]['nom_so_gar']
        ligne_u = G.nodes[u]['indice_lig']
        nom_v = G.nodes[v]['nom_so_gar']
        ligne_v = G.nodes[v]['indice_lig']
        afflu_u = get_affluence(nom_u, ligne_u, affluence_df, jour, heure)
        afflu_v = get_affluence(nom_v, ligne_v, affluence_df, jour, heure)
        afflu_moy = (afflu_u + afflu_v) / 2
        temps = 1.0  # Peut être raffiné plus tard
        weight = alpha * temps + beta * afflu_moy
        G[u][v]['weight'] = weight
        G[u][v]['flux'] = 0.0  # Trace bio-inspirée : quantité de flux ayant traversé cette arête

    # Initialisation du flux sur chaque nœud (tous à 0 sauf départ)
    node_flux = defaultdict(float)
    node_flux[start_station] = flux_init

    # Mémorisation des flux passés sur chaque arête pour analyse
    edge_flux_memory = defaultdict(float)

    for it in range(n_iter):
        next_node_flux = defaultdict(float)
        for node, flux in node_flux.items():
            if flux < 1e-6:
                continue
            neighbors = list(G.neighbors(node))
            if accessible_only:
                neighbors = [n for n in neighbors if G.nodes[n].get('Access', 1)]
            weights = []
            for n in neighbors:
                w = G[node][n]['weight']
                weights.append(1.0 / (w + 1e-6))
            weights = np.array(weights)
            if weights.sum() > 0:
                probs = weights / weights.sum()
            else:
                probs = np.ones_like(weights) / len(weights) if len(weights) > 0 else []
            for i, neighbor in enumerate(neighbors):
                flux_to_neighbor = (1-evaporation) * flux * probs[i]
                next_node_flux[neighbor] += flux_to_neighbor
                G[node][neighbor]['flux'] += flux_to_neighbor
                edge_flux_memory[(node, neighbor)] += flux_to_neighbor
        node_flux = next_node_flux

        # *** AJOUT DEBUG ***
        if verbose and it % 50 == 0:
            total_flux = sum(node_flux.values())
            touched_nodes = [n for n, f in node_flux.items() if f > 0]
            print(f"[Itération {it}] Flux total restant : {total_flux:.2f} — Noeuds actifs : {len(touched_nodes)}")
            if end_station in node_flux:
                print(f"  > Flux arrivé à la station d'arrivée ({end_station}) : {node_flux[end_station]:.2f}")



    if verbose:
            if end_station in node_flux and node_flux[end_station] > 0:
                print(f"Le flux est bien arrivé sur la station d'arrivée {end_station} ({node_flux[end_station]:.2f})")
    else:
        print(f"Aucun flux n'a atteint la station d'arrivée {end_station}.")
        # Affiche les voisins directs et le flux sur les arêtes qui mènent à l'arrivée
        preds = list(G.neighbors(end_station))
        print("Flux sur les arêtes menant à l'arrivée :")
        for pred in preds:
            if (pred, end_station) in edge_flux_memory:
                print(f"  {pred} -> {end_station} : {edge_flux_memory[(pred, end_station)]:.2f}")
            elif (end_station, pred) in edge_flux_memory:
                print(f"  {end_station} -> {pred} : {edge_flux_memory[(end_station, pred)]:.2f}")


    # Recherche du chemin le plus “renforcé” : on part du départ, à chaque étape on va vers le voisin qui a reçu le plus de flux, jusqu’à l’arrivée (greedy)
    chemin = [start_station]
    current = start_station
    total_score = 0.0
    visited = set()
    while current != end_station and len(chemin) < len(G):
        visited.add(current)
        neighbors = [n for n in G.neighbors(current) if n not in visited]
        if not neighbors:
            break
        # Prend le voisin avec le plus de flux reçu
        best_neighbor = max(neighbors, key=lambda n: G[current][n]['flux'])
        chemin.append(best_neighbor)
        total_score += G[current][best_neighbor]['weight']
        current = best_neighbor
        if current == end_station:
            break
    if current != end_station:
        if verbose:
            print("Le blob n’a pas trouvé d’arrivée.")
        return [], float('inf'), edge_flux_memory

    if verbose:
        print(f"BlobSolver exploré {len(edge_flux_memory)} arêtes, voici les flux principaux (top 10) :")
        sorted_edges = sorted(edge_flux_memory.items(), key=lambda x: -x[1])
        for (u, v), f in sorted_edges[:10]:
            print(f"{u} -> {v} : flux={f:.2f}")

    return chemin, total_score, edge_flux_memory
