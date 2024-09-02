from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import random
import deepl
import re
import numpy as np
from pydantic import BaseModel
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tensorflow_hub as hub
from sklearn.metrics.pairwise import cosine_similarity
import os
from ai21 import AI21Client

app = Flask(__name__)
CORS(app)

# Cargar el modelo desde TensorFlow Hub
model = hub.KerasLayer("https://tfhub.dev/google/nnlm-en-dim128/2")

# Autenticación para DeepL
auth_key = "fe66732a-52da-4432-9483-56c293dde951:fx"  # Reemplaza con tu clave
translator = deepl.Translator(auth_key)

# Inicializar el cliente de AI21
client = AI21Client(api_key="gyUZeCvly036HFJAYxVhLlHt0CDEryvB")

# Cargar el texto de entrada y dividirlo en fragmentos
def load_and_split_text(filename):
    with open(filename, 'r') as file:
        document_data = file.read().lower()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=220,
        chunk_overlap=10,
        length_function=len
    )

    return text_splitter.split_text(document_data)

# Traducir texto usando DeepL
def traductor(text, lang='EN-US'):
    result = translator.translate_text(text, target_lang=lang)
    return result.text

# Definir la entrada de datos para la API
class InputData(BaseModel):
    pregunta: str

# Cargar el texto y crear el vector store una vez

textsl = load_and_split_text('knowledge_base.txt')

# Datos para el saludo
user_saludo = ["buenos días", "buenos dias", "buenas tardes", "buenas noches", "hola", "ola", "hola!", "Hola", "Hola!", "buenas", "mucho gusto", "saludos"]
user_despedida = ["chau", "adios", "Adios", "nos vemos", "hasta pronto"]
user_gratitud = ["gracias", "Gracias", "agradezco", "graciass", "gracias.", "Gracias.", "garcias", "Garcias"]
bot_bienvenida = ["Somos la Universidad Nacional de Ingienería (UNI)👋\n ¿Como puedo ayudarlo?", "¡Saludos futuro universitario!😁\n¿Como puedo ayudarte?", "   ¡Mucho gusto!😊\nEstoy aquí para ayudar."]
bot_saludo = ["¡Hola, un gusto poder ayudarte", "¡Hola!", "¡Saludos!👋"]
bot_despedida = ["La disciplina es el puente entre las metas y el logro.\n¡Un gusto ayudarte!😀 ", "😀\n¡Hasta pronto!", "👋\n¡Nos Vemos!", "😄\nGracias por su tiempo ¡Nos vemos!👋"]
bot_gratitud = ["    ¡Estamos para ayudar!😄", "Para información más detallada puedes contactarnos por nuestras redes sociales.\n¡Suerte!😉", "¡Mucha suerte con tu postulamiento!😄"]
mensaje_aclaracion = ["Lo siento 😓\n¿Podrías ser más específico con tu pregunta?", "Perdón.\nNo encuentro respuesta a tu pregunta...\n¿Podrías brindarme más detalles?🤔"]

# FUNCIONES PURGANTES:
def questionCleaner(pregunta_traducida):
    innecesaryWords = ["Hello", "!", "hello", "thanks", "thank you", "thank you very much",
                       "Thanks", "Thank you very much", "Thank you", "?"]
    pattern = '|'.join(re.escape(phrase) for phrase in innecesaryWords)
    cleaned_text = re.sub(pattern, '', pregunta_traducida)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    return cleaned_text

def questionDataBaseCleaner(pregunta_traducida):
    innecesaryWords = [
        "and", "please", "your", "?", 
        "the", "of", "about", "what", "there", "in", "service",
        "provide", "with", "i", "need", "information", "on", "very",
        ",", "explain", "tell", "much", "me", ":", "a", "offer", "offered",
        "by", "like", "to", "hello", "can", "could", "would",
        "good", "want", "you", "explanation", "I", "as", "it", "for", 
        "available", "question", "they", "do"
    ]
    pattern = r'\b(?:' + '|'.join(re.escape(word) for word in innecesaryWords) + r')\b'
    cleaned_text = re.sub(pattern, '', pregunta_traducida)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    return cleaned_text

# Obtener los embeddings para cada frase
embeddings = model(textsl).numpy()

def Similarities(pregunta):
        new_embedding = model([pregunta]).numpy()
        similarities = cosine_similarity(new_embedding, embeddings)[0]
        top_indices = np.argsort(similarities)[-2:][::-1]
        top_phrases = [textsl[idx] for idx in top_indices]
        return top_phrases


@app.route("/", methods=["POST", "GET"])
def obtener_pregunta():
    data = request.get_json()
    pregunta = data.get('userInput').lower()
    pregunta_traducida = traductor(pregunta)
    dataBaseCleanedText = questionDataBaseCleaner(questionCleaner(pregunta_traducida))
    similarities = Similarities(dataBaseCleanedText)

    def windowsContext():
        windows_context = ''
        for i in similarities:
            windows_context += f"{i}\n\n"
        return windows_context

    windows_context = windowsContext()

    response = client.answer.create(
        context=windows_context,
        question=f"explain to me about, {questionCleaner(pregunta_traducida)}",
    )
    
    respuesta_US = response.answer
    respuesta = traductor(respuesta_US, 'ES') if respuesta_US else None

    for i in user_saludo:
        if i in pregunta:
            if not respuesta:
                respuesta = random.choice(bot_bienvenida)
            else:
                respuesta = f"{random.choice(bot_saludo)}\n{respuesta}"
            break
    else:
        for j in user_despedida:
            if j in pregunta:
                if not respuesta:
                    respuesta = random.choice(bot_despedida)
                else:
                    respuesta = f"{respuesta}\n{random.choice(bot_despedida)}"
                break
        else:
            for x in user_gratitud:
                if x in pregunta:
                    if not respuesta:
                        respuesta = random.choice(bot_gratitud)
                    else:
                        respuesta = f"{respuesta}\n\n{random.choice(bot_gratitud)}"
                    break
            if not respuesta:
                respuesta = random.choice(mensaje_aclaracion)

    return jsonify({"respuesta": respuesta})

if __name__ == "__main__":
    app.run(debug=True)
