# frontend.py
import tkinter as tk
from tkinter import scrolledtext
import openai
import pyttsx3
import speech_recognition as sr
from threading import Thread
import smtplib
import ssl
from email.message import EmailMessage
from config import apikey
from main import init_speech_recognizer, init_tts_engine, email_sender, send_email

# Import other functions and constants as needed

openai.api_key = apikey

# Initialize the text-to-speech engine and speech recognizer
engine = init_tts_engine()
recognizer = init_speech_recognizer()

# Initialize conversation history and voice command mode
conversation_history = []
voice_command_mode = False

# Create the main GUI window
root = tk.Tk()
root.title("Nisha - Your Substation Maintenance Partner")

# Create a scrolled text widget to display the conversation history
conversation_text = scrolledtext.ScrolledText(root, width=50, height=20)
conversation_text.pack()

# Create an entry widget for user input
user_input_entry = tk.Entry(root, width=50)
user_input_entry.pack()


# Function to handle text input
def handle_text_input():
    user_input_text = user_input_entry.get().strip().lower()
    user_input_entry.delete(0, tk.END)
    handle_user_input(user_input_text)


# Function to handle voice input
def handle_voice_input():
    def listen_and_recognize():
        global voice_command_mode
        voice_command_mode = True
        with sr.Microphone() as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source)
        try:
            user_input_voice = recognizer.recognize_google(audio, language="en-in")
            handle_user_input(user_input_voice)
        except sr.UnknownValueError:
            print("You (Voice): (Silence)")
        except sr.RequestError:
            print("You (Voice): Sorry, there was an issue connecting to Google's servers.")
            speak("Sorry, there was an issue connecting to Google's servers.")
        voice_command_mode = False

    Thread(target=listen_and_recognize).start()


# Function to handle user input (both text and voice)
def handle_user_input(user_input):
    global conversation_history
    conversation_history.append(f"You: {user_input}")
    conversation_text.insert(tk.END, f"You: {user_input}\n")
    conversation_text.yview(tk.END)

    if user_input == 'exit' or user_input == 'quit':
        send_summary_email()
        speak("Goodbye!")
        root.destroy()
    elif 'your name' in user_input:
        speak("My name is Nisha. How can I help you?")
    elif '`' in user_input:
        handle_voice_input()
    elif 'send an email' in user_input:
        recipient = input("Recipient: ")
        subject = input("Subject: ")
        message = input("Message: ")
        send_email(subject, message, recipient)
    else:
        generate_and_speak_response(user_input)


# Function to send a summary email
def send_summary_email():
    subject = 'Nisha Conversation Summary'
    body = 'List of Maintenance Queries\n\n' + '\n\n'.join(conversation_history)
    send_email(subject, body, email_sender)
    speak("Email sent successfully!")


# Function to generate and speak a response
def generate_and_speak_response(input_text):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=input_text,
        max_tokens=500,
        temperature=0.38,
        top_p=1,
        frequency_penalty=1,
        presence_penalty=1
    )

    nisha_response = response.choices[0].text.strip()
    conversation_history.append(f"Nisha: {nisha_response}")
    conversation_text.insert(tk.END, f"Nisha: {nisha_response}\n")
    conversation_text.yview(tk.END)
    speak(nisha_response)


# Function to speak a message using text-to-speech
def speak(message):
    engine.say(message)
    engine.runAndWait()


# Create buttons for text and voice input
text_input_button = tk.Button(root, text="Text Input", command=handle_text_input)
voice_input_button = tk.Button(root, text="Voice Input", command=handle_voice_input)
text_input_button.pack()
voice_input_button.pack()

# Start the GUI main loop
root.mainloop()
