from blobia.utils import load_monuments, load_stations, load_affluence_stations
from blobia.graph_builder import build_metro_graph
from blobia.blob_solver import blob_solver_bioinspire
from blobia.utils import load_monuments, load_stations, load_affluence_stations, propagate_affluence



def main():
    # Nom de la station de départ (à adapter)
    nom_depart = "Aéroport d'Orly"
    monument_arrivee = "Jardin de la Tour Effeil"
    jour = "Lundi"
    heure = 7
    curseur = 10
    accessible_only = False

    alpha = (11 - curseur) / 10
    beta = curseur / 10

    #Chargement des données
    stations_df = load_stations()
    monuments_df = load_monuments()
    affluence_stations_df = load_affluence_stations()

    # Harmoniser le nom de la colonne
    affluence_stations_df = affluence_stations_df.rename(columns={"Gare": "Nom station"})

    # Merge pour ajouter la colonne Ligne
    stations_df_min = stations_df[["nom_so_gar", "indice_lig"]].drop_duplicates()
    stations_df_min = stations_df_min.rename(columns={
        "nom_so_gar": "Nom station",
        "indice_lig": "Ligne"
    })
    affluence_stations_df = affluence_stations_df.merge(
        stations_df_min,
        on="Nom station",
        how="left"
    )

    # Lancer la propagation de l'affluence
    affluence_stations_df = propagate_affluence(affluence_stations_df)



    # Chercher la station de départ (prend la première ligne dispo)
    possible_stations = stations_df[stations_df['nom_so_gar'] == nom_depart]
    if possible_stations.empty:
        raise ValueError(f"Aucune station nommée '{nom_depart}' trouvée dans les données.")
    gare_depart = f"{possible_stations.iloc[0]['nom_so_gar']}|{possible_stations.iloc[0]['indice_lig']}"
    print(f"Station de départ sélectionnée : {gare_depart}")

    # Chercher la station la plus proche du monument
    filt = (monuments_df['Monument'] == monument_arrivee)
    if jour: filt &= (monuments_df['Jour'] == jour)
    if heure: filt &= (monuments_df['Heure'] == heure)
    subset = monuments_df[filt]
    if subset.empty:
        raise ValueError("Pas de correspondance monument/jour/heure trouvée.")
    station_arrivee = subset.iloc[0]['Station la plus proche']
    distance_pied = subset.iloc[0]['Distance à pied (m)']

    # Récupérer le premier noeud station|ligne correspondant pour l'arrivée
    station_arrivee_id = None
    for idx, row in stations_df[stations_df['nom_so_gar'] == station_arrivee].iterrows():
        station_arrivee_id = f"{row['nom_so_gar']}|{row['indice_lig']}"
        break

    if station_arrivee_id is None:
        raise ValueError(f"Station d'arrivée '{station_arrivee}' introuvable dans les gares.")

    # Construction du graphe
    G = build_metro_graph(stations_df)

    # Vérification des nœuds
    if gare_depart not in G.nodes:
        raise ValueError(f"La station de départ '{gare_depart}' n'existe pas dans le graphe. Format attendu : 'nom_so_gar|indice_lig'")
    if station_arrivee_id not in G.nodes:
        raise ValueError(f"La station d'arrivée '{station_arrivee_id}' n'existe pas dans le graphe.")

    print(f"Départ : {gare_depart}\nArrivée : {monument_arrivee} (station la plus proche : {station_arrivee}, {distance_pied:.0f} m à pied)")

    # Algorithme Blob IA (utilise affluence_stations_df)
    chemin, score, fluxes = blob_solver_bioinspire(
        G, 
        start_station=gare_depart, 
        end_station=station_arrivee_id,
        affluence_df=affluence_stations_df,
        jour=jour,
        heure=heure,
        alpha=alpha,
        beta=beta,
        accessible_only=accessible_only,
        n_iter=60,        # tu peux tester 30, 50, 100, etc.
        flux_init=2000,   # quantité de flux au départ
        evaporation=0.12, # taux de perte à chaque vague
     verbose=True      # pour voir le log
    )
    

    if chemin:
        print(f"Chemin trouvé : {' -> '.join(chemin)}")
        print(f"Nombre de stations : {len(chemin)-1}")
        print(f"Score du chemin : {score:.2f}")
    else:
        print("Aucun chemin possible avec les contraintes données.")

if __name__ == "__main__":
    main()
