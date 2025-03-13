
# API Recommandation Événements

## Lancement local
```bash
pip install django pandas scikit-learn
python manage.py runserver
```

## Appel API
- URL : `/api/recommandations/?user_id=U1&top_n=5`
- Méthode : GET
- Réponse : JSON liste d'événements recommandés

## Notes
- Placer les fichiers CSV dans la racine : `df_reservation_par_pers.csv`, `bdd_final_event.csv`
- Ajouter votre moteur de recommandation complet dans `recommandations/views.py`
