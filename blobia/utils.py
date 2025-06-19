import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def load_monuments(filename='BDD Monument Gare Affluence.csv'):
    """Charge le fichier des monuments et stations associées."""
    path = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(path)
    return df

def load_stations(filename='emplacement-des-gares-idf.csv'):
    """Charge le fichier des gares/stations du réseau."""
    path = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(path)
    return df
