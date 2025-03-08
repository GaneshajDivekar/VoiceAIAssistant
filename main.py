import os
import requests
from fastapi import FastAPI, Form
from twilio.twiml.voice_response import VoiceResponse
from gtts import gTTS
import speech_recognition as sr
import uvicorn

app = FastAPI()

# Twilio & Mistral Credentials (Set these in Environment Variables)
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER", "+14638007696")  # Replace with your Twilio number
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "pelioXQkD8OfhfXrOzTLlMhBKmowOJj8")

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# Enhanced Static Banking Data
BANKING_DATA = {
    "name": "Ganesh Divekar",
    "account_number": "123456789",
    "balance": 50000.75,
    "ifsc_code": "HDFC0000123",
    "branch": "Shivaji Nagar, Pune",
    "credit_card_due": 8000,
    "loan_emi": 5000,
    "transactions": [
        {"date": "2024-03-01", "type": "debit", "amount": 2000, "description": "ATM Withdrawal"},
        {"date": "2024-03-05", "type": "credit", "amount": 10000, "description": "Salary Credit"},
        {"date": "2024-03-10", "type": "debit", "amount": 1500, "description": "Online Shopping"},
        {"date": "2024-03-15", "type": "debit", "amount": 2500, "description": "Electricity Bill"},
        {"date": "2024-03-20", "type": "credit", "amount": 5000, "description": "Freelance Payment"},
    ],
}

@app.post("/voice")
def handle_call():
    """Handles incoming calls from Twilio."""
    response = VoiceResponse()
    response.say("Welcome to Ganesh's AI Banking Assistance. Please state your query after the beep.")
    response.record(max_length=10, action="/process-voice")
    return str(response)

@app.post("/process-voice")
def process_voice(recording_url: str = Form(...)):
    """Processes the recorded voice message."""
    response = VoiceResponse()

    # Convert Speech to Text
    recognizer = sr.Recognizer()
    audio_file = requests.get(recording_url).content
    with open("audio.wav", "wb") as f:
        f.write(audio_file)

    with sr.AudioFile("audio.wav") as source:
        audio = recognizer.record(source)

    try:
        text_query = recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        response.say("Sorry, I could not understand. Please try again.")
        return str(response)

    # Get AI response
    ai_response = get_ai_response(text_query)

    # Convert AI response to Speech
    tts = gTTS(text=ai_response, lang="en")
    tts.save("response.mp3")

    # Play Response
    response.play("/response.mp3")
    return str(response)

def get_ai_response(query):
    """Handles user queries using static banking data before calling Mistral AI."""
    query_lower = query.lower()

    # Check for specific banking queries
    if "balance" in query_lower or "how much money" in query_lower:
        return f"Your current balance is {BANKING_DATA['balance']} rupees."

    elif "recent transactions" in query_lower or "last transactions" in query_lower:
        transactions = BANKING_DATA["transactions"][:3]  # Get last 3 transactions
        response_text = "Here are your last 3 transactions: "
        for txn in transactions:
            response_text += f"On {txn['date']}, {txn['type']} of {txn['amount']} rupees for {txn['description']}. "
        return response_text

    elif "account number" in query_lower:
        return f"Your account number is {BANKING_DATA['account_number']}."

    elif "ifsc code" in query_lower:
        return f"Your IFSC code is {BANKING_DATA['ifsc_code']}."

    elif "branch" in query_lower:
        return f"Your account is in {BANKING_DATA['branch']} branch."

    elif "credit card due" in query_lower:
        return f"Your current credit card due is {BANKING_DATA['credit_card_due']} rupees."

    elif "loan emi" in query_lower:
        return f"Your loan EMI is {BANKING_DATA['loan_emi']} rupees per month."

    # If no banking match, use Mistral AI to generate a response
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}"}
    payload = {"prompt": query, "temperature": 0.7, "max_tokens": 200}
    response = requests.post("https://api.mistral.ai/v1/generate", json=payload, headers=headers)

    if response.status_code == 200:
        return response.json().get("choices", [{}])[0].get("text", "I am unable to respond at the moment.")
    else:
        return "Error fetching response."

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
