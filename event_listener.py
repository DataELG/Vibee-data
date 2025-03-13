import psycopg2
import select
import json
import requests

# Informations de connexion à la base PostgreSQL
DB_NAME = "bjzv0bfpzgquhzxmjzuo"
USER = "u2puh0fcouhfbwcpvqu3"
PASSWORD = "HxTong235uPHl0yjUIRM6qRLfCRkpi"
HOST = "bjzv0bfpzgquhzxmjzuo-postgresql.services.clever-cloud.com"
PORT = "50013"

API_URL = "http://127.0.0.1:8000/generate_summary/"

# Connexion à la base PostgreSQL
conn = psycopg2.connect(dbname=DB_NAME, user=USER, password=PASSWORD, host=HOST, port=PORT)
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

# Écouter les notifications sur le canal "new_event"
cur.execute("LISTEN new_event;")
print("Écoute en cours des nouveaux événements...")

# Boucle d'écoute des notifications PostgreSQL
while True:
    conn.poll()
    while conn.notifies:
        notify = conn.notifies.pop(0)
        
        try:
            event_data = json.loads(notify.payload)  # Convertit le JSON en dictionnaire
            event_name = event_data["events"]  # Récupération du nom de l'événement
            
            print(f"Nouvel événement détecté : {event_data}")

            # Envoi des données à l'API de génération de résumé
            response = requests.post(API_URL, json=event_data)

            if response.status_code == 200:
                summary = response.json().get("summary_fr", "")
                
                if summary:
                    update_query = 'UPDATE "Events" SET "Summary" = %s WHERE "Nom" = %s'
                    cur.execute(update_query, (summary, event_data["events"]))
                    print(f"Résumé mis à jour pour {event_data['events']}")

        except Exception as e:
            print(f"Erreur : {e}")

print("En attente de nouveaux événements...")

while True:
    select.select([conn], [], [])
    conn.poll()
