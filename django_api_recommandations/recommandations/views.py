
import pandas as pd
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ast import literal_eval
from datetime import datetime
from django.http import JsonResponse
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger .env
load_dotenv()

TOKEN = os.environ.get('TOKEN')
API_URL_RESERVATION = os.environ.get('API_URL_RESERVATION')
API_URL_EVENT = os.environ.get('API_URL_EVENT')


def login_event():
    api_url = API_URL_EVENT
    bearer_token = TOKEN
    # En-têtes de la requête avec le token Bearer
    headers = {
        'Authorization': f'Bearer {bearer_token}'
    }
    
    # Faire l'appel GET avec l'en-tête Authorization
    response = requests.get(api_url, headers=headers)
    
    # Vérifier la réponse
    if response.status_code == 200:
        #print("Réponse de l'API :", response.json())
        return response.json()
    else:
        print(f"Erreur : {response.status_code}, {response.text}")


def login_reservation():
    api_url = API_URL_RESERVATION
    bearer_token = TOKEN
    # En-têtes de la requête avec le token Bearer
    headers = {
        'Authorization': f'Bearer {bearer_token}'
    }
    
    # Faire l'appel GET avec l'en-tête Authorization
    response = requests.get(api_url, headers=headers)
    
    # Vérifier la réponse
    if response.status_code == 200:
        #print("Réponse de l'API :", response.json())
        return response.json()
    else:
        print(f"Erreur : {response.status_code}, {response.text}")


# Upload dataset
# df_resa = pd.read_csv('/Users/manu/Desktop/SUP/Semaine Campus/OUTPUT/bdd_resa.csv')
# df_evenements = pd.read_csv('/Users/manu/Desktop/SUP/Semaine Campus/OUTPUT/bdd_final_event_.csv')
df_resa = pd.DataFrame(login_reservation())
df_evenements = pd.DataFrame(login_event())
df_users = pd.read_csv('/Users/manu/Desktop/SUP/Semaine Campus/OUTPUT/bdd_users.csv')

# Create df_reservations
df_reservations = pd.merge(df_resa, df_evenements,
                           how = 'left',
                           left_on = 'eventId',
                           right_on = 'id')

# Preprocess
def safe_literal_eval(val):
    try:
        if pd.isnull(val):
            return []
        res = literal_eval(val)
        return res if isinstance(res, list) else [str(res)]
    except (ValueError, SyntaxError):
        return [val] if isinstance(val, str) else []

df_reservations['Tags'] = df_reservations['Tags'].apply(safe_literal_eval)
df_evenements['Tags'] = df_evenements['Tags'].apply(safe_literal_eval)

# Keep upcoming events
today = pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))

df_evenements['DateDebut'] = pd.to_datetime(df_evenements['DateDebut'], errors='coerce')
# Vérifier et retirer timezone si elle existe
if pd.api.types.is_datetime64_any_dtype(df_evenements['DateDebut']):
    try:
        df_evenements['DateDebut'] = df_evenements['DateDebut'].dt.tz_localize(None)
    except TypeError:
        # Si déjà tz-naive, rien à faire
        pass
df_evenements_futurs = df_evenements[df_evenements['DateDebut'] >= today].copy()

# Create user profile
def create_user_profile(user_id):
    user_reservations = df_reservations[df_reservations['userId'] == user_id]
    all_tags = [tag for tags_list in user_reservations['Tags'] for tag in tags_list]
    tag_freq = pd.Series(all_tags).value_counts().to_dict()
    all_descriptions = ' '.join(user_reservations['Description'].dropna().tolist())
    price_map = {'GRATUIT': 0, 'PAYANT': 1}
    prices = user_reservations['Tarif'].map(price_map).dropna().astype(int)
    avg_price = prices.mean() if not prices.empty else 0.5
    return tag_freq, all_descriptions, avg_price

# Jacard similarity pour les tags
def tag_similarity(tags_user, tags_event):
    set_user, set_event = set(tags_user.keys()), set(tags_event)
    intersection, union = len(set_user & set_event), len(set_user | set_event)
    return intersection / union if union > 0 else 0

# price similarity
def price_similarity(user_price, event_price):
    price_map = {'GRATUIT': 0, 'PAYANT': 1}
    event_price_num = price_map.get(event_price, 0.5)
    return 1 if user_price == event_price_num else 0

# Moteur de recommandation complet (avec dédoublonnage et diversité)
def compute_recommendations_advanced(user_id, top_n=5, max_per_category=2):
    user_tags, user_description, user_avg_price = create_user_profile(user_id)
    df_events = df_evenements_futurs.reset_index(drop=True)

    # TF-IDF sur la description
    corpus = df_events['Description'].fillna('').tolist() + [user_description]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)
    user_vec, event_vecs = tfidf_matrix[-1], tfidf_matrix[:-1]
    description_similarities = cosine_similarity(user_vec, event_vecs).flatten()

    # Calcul des scores
    scores = []
    for idx, row in df_events.iterrows():
        tags_score = tag_similarity(user_tags, row['Tags'])
        price_score = price_similarity(user_avg_price, row['Tarif'])
        desc_score = description_similarities[idx]
        final_score = (0.3 * tags_score) + (0.1 * price_score) + (0.6 * desc_score)
        scores.append((idx, row['id'], final_score, row['Nom'], row['Tags']))

    # Trier et dédupliquer par nom d'événement
    sorted_scores = sorted(scores, key=lambda x: x[2], reverse=True)
    seen_event_names, unique_events = set(), []
    for idx, event_id, score, event_name, tags in sorted_scores:
        if event_name not in seen_event_names:
            unique_events.append((idx, event_id, score, event_name, tags))
            seen_event_names.add(event_name)

    # Limiter par catégorie principale (1er tag comme catégorie principale)
    category_counts, final_selection = {}, []
    for idx, event_id, score, event_name, tags in unique_events:
        if not tags: continue  # Si pas de tags on saute
        main_category = tags[0]
        if category_counts.get(main_category, 0) < max_per_category:
            final_selection.append((idx, event_id, score))
            category_counts[main_category] = category_counts.get(main_category, 0) + 1
        if len(final_selection) >= top_n:
            break

    # Sélection finale des événements
    selected_indices = [idx for idx, _, _ in final_selection]
    recommended_events = df_events.loc[selected_indices]

    # Format JSON-like
    recommendations = recommended_events[['id', 'Nom', 'Description', 'Tags', 'Tarif', 'DateDebut', 'Lieu', 'Image']].to_dict(orient='records')
    return recommendations


# API pour l'app mobile
def get_recommendations(request):
    user_id = request.GET.get('userId')
    top_n = int(request.GET.get('top_n', 5))  # Valeur par défaut 5

    if not user_id:
        return JsonResponse({'error': 'user_id est requis'}, status=400)

    try:
        result = compute_recommendations_advanced(user_id, top_n=top_n)
        return JsonResponse(result, safe=False, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
