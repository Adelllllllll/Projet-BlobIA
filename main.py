from blobia.utils import load_monuments, load_stations
from blobia.graph_builder import build_metro_graph
from blobia.blob_solver import blob_solver

def main():
    # Paramètres de test (personnalisables)
    gare_depart = "Aéroport d'Orly"                    # DOIT être une station présente dans 'stations_df'
    monument_arrivee = "Jardin de la Tour Effeil"  # DOIT être un monument présent dans 'monuments_df'
    jour = "Lundi"
    heure = 9
    curseur = 1
    accessible_only = False

    alpha = (11 - curseur) / 10
    beta = curseur / 10

    # Chargement des données
    stations_df = load_stations()
    monuments_df = load_monuments()

    # Chercher la station la plus proche du monument
    filt = (monuments_df['Monument'] == monument_arrivee)
    if jour: filt &= (monuments_df['Jour'] == jour)
    if heure: filt &= (monuments_df['Heure'] == heure)
    subset = monuments_df[filt]
    if subset.empty:
        raise ValueError("Pas de correspondance monument/jour/heure trouvée.")
    station_arrivee = subset.iloc[0]['Station la plus proche']
    distance_pied = subset.iloc[0]['Distance �� pied (m)']
    
    print(f"Départ : {gare_depart}\nArrivée : {monument_arrivee} (station la plus proche : {station_arrivee}, {distance_pied:.0f} m à pied)")

    # Construction du graphe
    G = build_metro_graph(stations_df)

    # Algorithme Blob IA
    chemin, score = blob_solver(
        G, 
        start_station=gare_depart, 
        end_station=station_arrivee,
        affluence_df=monuments_df,
        jour=jour, 
        heure=heure,
        alpha=alpha, 
        beta=beta, 
        accessible_only=accessible_only
    )

    print(f"Chemin trouvé : {' -> '.join(chemin)}")
    print(f"Nombre de stations : {len(chemin)-1}")
    print(f"Score du chemin : {score:.2f}")


if __name__ == "__main__":
    main()
