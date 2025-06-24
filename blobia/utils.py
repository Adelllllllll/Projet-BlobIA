import pandas as pd
import os
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def load_monuments(filename='BDD Monument Gare Affluence.csv'):
    """Charge le fichier des monuments et stations associées."""
    path = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(path)
    # Corriger nom de colonne si mauvais encodage
    if 'Distance �� pied (m)' in df.columns:
        df = df.rename(columns={'Distance �� pied (m)': 'Distance à pied (m)'})
    return df

def load_stations(filename='emplacement-des-gares-idf.csv'):
    """Charge le fichier des gares/stations du réseau."""
    path = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(path)
    return df

def load_affluence_stations(filename='affluence_stations_paris.xlsx'):
    """Charge le fichier Excel d'affluence horaire par station."""
    path = os.path.join(DATA_DIR, filename)
    df = pd.read_excel(path)
    return df


def propagate_affluence(affluence_df, reduction_coeff=0.8, max_iter=10):
    """
    Propage l'affluence connue aux stations voisines sans donnée.
    À chaque itération, une station sans donnée prend 0.8* la plus grande affluence de ses voisines connues (même ligne, même jour, même heure).
    """
    df = affluence_df.copy()
    # On travaille sur chaque (Ligne, Jour, Heure) séparément
    group_cols = ['Ligne', 'Jour', 'Heure']
    if not all(col in df.columns for col in group_cols + ['Nom station', 'Affluence']):
        raise ValueError("Le DataFrame d'affluence doit contenir les colonnes ['Ligne', 'Nom station', 'Jour', 'Heure', 'Affluence']")
    
    for key, group in df.groupby(group_cols):
        idxs_no_aff = group[group['Affluence'].isna()].index.tolist()
        idxs_with_aff = group[~group['Affluence'].isna()].index.tolist()
        # Propagation par voisinage sur la même ligne, pour chaque créneau
        iter_count = 0
        while idxs_no_aff and iter_count < max_iter:
            changed = False
            for idx in idxs_no_aff:
                # Cherche les voisins directs sur la même ligne, même jour/heure (prends stations adjacentes par l'index dans le groupe)
                pos = group.index.get_loc(idx)
                neighbor_affluences = []
                if pos > 0:
                    left_idx = group.index[pos - 1]
                    left_aff = group.loc[left_idx, 'Affluence']
                    if not pd.isna(left_aff):
                        neighbor_affluences.append(left_aff)
                if pos < len(group) - 1:
                    right_idx = group.index[pos + 1]
                    right_aff = group.loc[right_idx, 'Affluence']
                    if not pd.isna(right_aff):
                        neighbor_affluences.append(right_aff)
                if neighbor_affluences:
                    df.at[idx, 'Affluence'] = max(neighbor_affluences) * reduction_coeff
                    changed = True
            # Recalcule les listes pour la prochaine itération
            group = df.loc[group.index]
            idxs_no_aff = group[group['Affluence'].isna()].index.tolist()
            iter_count += 1
            if not changed:
                break
    return df
