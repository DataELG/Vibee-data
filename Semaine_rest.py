from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, M2M100ForConditionalGeneration, M2M100Tokenizer

# Initialisation de FastAPI
app = FastAPI()

# Modèles NLP
GENERATION_MODEL_NAME = "facebook/bart-large-cnn"
TRANSLATION_MODEL_NAME = "facebook/m2m100_418M"

tokenizer_summary = AutoTokenizer.from_pretrained(GENERATION_MODEL_NAME)
generation_model = AutoModelForSeq2SeqLM.from_pretrained(GENERATION_MODEL_NAME)

tokenizer_translation = M2M100Tokenizer.from_pretrained(TRANSLATION_MODEL_NAME)
translation_model = M2M100ForConditionalGeneration.from_pretrained(TRANSLATION_MODEL_NAME)

# Modèle de données pour l'entrée API
class EventData(BaseModel):
    events: str
    place: str
    tags: str
    fetch_price: str
    description: str
    adress: str
    date_debut: str
    date_fin: str

# Fonction de résumé
def summarize_documents(documents):
    context = f"""
    Title: {documents.events}
    Location: {documents.place}
    Tags: {documents.tags}
    Price Type: {documents.fetch_price}
    Description: {documents.description}
    Address: {documents.adress}
    Beginning Date: {documents.date_debut}
    Ending Date: {documents.date_fin}
    """

    input_text = f"""
    Below is information about an event:

    {context}

    Summarize this event **creatively and concisely** in **natural language**.  
    - Begin with the **event title**.  
    - Describe its **purpose** in a **new way** (do not copy the description).  
    - Conclude with the **location and date**.

    ⚠️ **Do NOT copy the description. Reformulate it.**
    """

    inputs = tokenizer_summary(input_text, return_tensors="pt", truncation=True, max_length=512)
    outputs = generation_model.generate(**inputs, max_length=150, num_beams=5, early_stopping=True)
    summary = tokenizer_summary.decode(outputs[0], skip_special_tokens=True)
    
    return summary

# Fonction de traduction en français
def translate_to_french(text):
    inputs = tokenizer_translation(text, return_tensors="pt", src_lang="en")
    translated_tokens = translation_model.generate(**inputs, forced_bos_token_id=tokenizer_translation.get_lang_id("fr"))
    translated_text = tokenizer_translation.decode(translated_tokens[0], skip_special_tokens=True)

    return translated_text

# Endpoint API pour générer un résumé
@app.post("/generate_summary/")
async def generate_summary(event: EventData):
    summary_en = summarize_documents(event)
    summary_fr = translate_to_french(summary_en)

    return {summary_fr}