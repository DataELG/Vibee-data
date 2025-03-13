import re
import pandas as pd
from datetime import datetime
import requests


def fetch_adress(coordinates_list):
    # Sécurisation du format
    if not isinstance(coordinates_list, (list, tuple)) or len(coordinates_list) != 2:
        return None
    
    try:
        lon, lat = map(float, coordinates_list)  # On force en float au cas où ce serait des strings
        
        url = f'https://api-adresse.data.gouv.fr/reverse/?lon={lon}&lat={lat}'
        response = requests.get(url)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        # Vérifie si 'features' existe et contient au moins un élément
        features = data.get('features', [])
        if not features:
            return None
        
        properties = features[0].get('properties', {})
        rue = properties.get('name', '')
        postcode = properties.get('postcode', '')
        city = properties.get('city', '')
        
        # Formater proprement l'adresse
        adresse = ', '.join(part for part in [rue, postcode, city] if part).strip()
        return adresse if adresse else None
    
    except Exception as e:
        return None

# Dictionnaire de correspondance des mois français
mois_fr = {
    'JANV.': 1, 'FEV.': 2, 'FÉV.': 2, 'MARS': 3, 'MAR' : 3, 'MAR.' : 3,'AVR.': 4, 
    'AVR': 4, 'MAI': 5, 'JUIN': 6, 'JUIL.': 7, 'AOÛT': 8,
    'SEPT.': 9, 'OCTOBRE': 10, 'NOV.': 11, 'NOVEMBRE' : 11, 'DÉC.': 12, 'DEC.': 12, 'DÉCEMBRE' :12
}

# Fonction d'extraction et de transformation
def extraire_dates(periode):
    annee = 2025
    
    if not periode or not isinstance(periode, str):
        return pd.Series([None, None])
    
    if periode.upper().startswith('DU'):
        match = re.search(r'DU (\d{1,2}) (\w+)\s+AU (\d{1,2}) (\w+)', periode, re.IGNORECASE)
        if match:
            jour_debut, mois_debut, jour_fin, mois_fin = match.groups()
            mois_debut_num = mois_fr.get(mois_debut.upper())
            mois_fin_num = mois_fr.get(mois_fin.upper())

            if mois_debut_num and mois_fin_num:
                try:
                    date_debut = datetime(annee, mois_debut_num, int(jour_debut))
                    date_fin = datetime(annee, mois_fin_num, int(jour_fin))
                    return pd.Series([date_debut, date_fin])
                except ValueError as e:
                    print(f"Erreur de date pour '{periode}': {e}")
                    return pd.Series([None, None])
    
    else:
        match = re.search(r'(\d{1,2})\s*(\w+)', periode)
        if match:
            jour, mois = match.groups()
            mois_num = mois_fr.get(mois.upper())

            if mois_num:
                try:
                    date = datetime(annee, mois_num, int(jour))
                    return pd.Series([date, date])  
                except ValueError as e:
                    print(f"Erreur de date pour '{periode}': {e}")
                    return pd.Series([None, None])
    
    # Si aucun cas ne matche ou mois inconnu
    return pd.Series([None, None])


def create_date_debut(row):
    heure = row['Heure de début'] if pd.notnull(row['Heure de début']) else '00:00'  # Heure par défaut si vide
    date_str = f"{row['DateFin']} {heure}"
    try:
        return pd.to_datetime(date_str, format='%Y-%m-%d %H:%M')
    except:
        return pd.NaT

def create_date_fin(row):
    date_str = f"{row['DateFin']} 23:59:59"
    try:
        return pd.to_datetime(date_str, format='%Y-%m-%d %H:%M:%S')
    except:
        return pd.NaT
