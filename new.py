import os
import re
import pyttsx3
import speech_recognition as sr
from googlesearch import search
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import google.auth.exceptions
from google_auth_oauthlib import flow
from config import apikey
from llama_index import SimpleDirectoryReader, GPTSimpleVectorIndex, LLMPredictor, PromptHelper, ServiceContext
from langchain import OpenAI
import openai
from config import secrets
import logging

# Set the OpenAI API key
os.environ["OPENAI_API_KEY"] = apikey  # Replace with your OpenAI API key

# OAuth2 credentials file path
CLIENT_SECRETS_FILE = secrets  # Replace with your OAuth2 credentials file

# Gmail email addresses
EMAIL_ADDRESS = "anshumanacadmic@gmail.com"  # Replace with your Gmail email address
SUPERIOR_EMAIL = "findmeansh@gmail.com"  # Replace with your superior's Gmail email address

# Initialize a conversation history list
conversation_history = []

# Initialize the OpenAI API client
openai.api_key = os.environ["OPENAI_API_KEY"]

# Initialize the OAuth2 flow variable
oauth_flow = None

# Set up logging
logging.basicConfig(filename='quantum.log', level=logging.DEBUG, format='%(pastime)s - %(levelness)s - %(message)s')
logging.info("Quantum: Hello, I am Quantum")


# Function to create an index of text documents
def construct_index(directory_path):
    # Set parameters for the text index
    max_input_size = 4096
    num_outputs = 2000
    max_chunk_overlap = 20
    chunk_size_limit = 600

    # Initialize the LLAMA index components
    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)
    llm_predictor = LLMPredictor(llm=OpenAI(temperature=0.5, model_name="text-davinci-003", max_tokens=num_outputs))

    # Load documents from the specified directory
    documents = SimpleDirectoryReader(directory_path).load_data()

    # Create the LLAMA index
    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, prompt_helper=prompt_helper)
    index = GPTSimpleVectorIndex.from_documents(documents, service_context=service_context)

    index.save_to_disk('index.json')

    return index


# Function to chat with a bot using the text index
# Function to chat with a bot using the text index
def chat_with_bot(index, user_input=None, conversation_history=None):
    if conversation_history is None:
        conversation_history = []  # Create a new list if conversation_history is None
    conversation_history_text = '\n'.join(conversation_history)
    combined_input = conversation_history_text + '\nUser: ' + user_input
    response = index.query(combined_input)

    if response is not None and response.response is not None:
        response_text = re.sub(r'<.*?>', '', response.response).strip()
        print("Quantum:", response_text)
        say("Quantum says: " + response_text)

        # Check if the new response is the same as the previous response
        # todo change parameter for quantum model
        if conversation_history and conversation_history[-1].startswith("Quantum:"):
            previous_response = conversation_history[-1][8:]  # Extract the previous response text
            if response_text == previous_response:
                print("Quantum: I won't repeat the same response.")
                say("I won't repeat the same response.")
            else:
                conversation_history.append("User: " + user_input)
                conversation_history.append("Quantum: " + response_text)
        else:
            conversation_history.append("User: " + user_input)
            conversation_history.append("Quantum: " + response_text)
    else:
        print("Quantum: Sorry, I couldn't generate a response for that.")
        say("Sorry, I couldn't generate a response for that.")


# Function to convert text to speech and speak it
def say(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


# Function to recognize voice commands
def takeCommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.pause_threshold = 1
        audio = r.listen(source)
        try:
            query = r.recognize_google(audio, language="en-in")
            print(f"you said: {query}")
            say(f"You said: {query}")
            return query
        except sr.UnknownValueError:
            print("Sorry, I didn't understand what you said.")
            say("Sorry, I didn't understand what you said.")
            return ""
        except sr.RequestError:
            print("Sorry, there was an issue connecting to Google's servers.")
            say("Sorry, there was an issue connecting to Google's servers.")
            return ""


# Function to perform a Google search and return results
def google_search(query, num_results=5):
    results = list(search(query, num_results=num_results))
    return results


# Function to query OpenAI's knowledge base
def openai_search(query, max_tokens=50):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=query,
        max_tokens=max_tokens,
        n=1
    )
    return response.choices[0].text


# Function to send an email summary of the conversation
def send_summary_email(conversation_history):
    global oauth_flow
    try:
        if oauth_flow is None:
            oauth_flow = flow.InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=['https://www.googleapis.com/auth/gmail.send']
            )

        creds = oauth_flow.run_local_server(port=0)

        service = build('gmail', 'v1', credentials=creds)

        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = SUPERIOR_EMAIL
        msg["Subject"] = "Conversation Summary with Quantum"

        conversation_text = "\n".join(conversation_history)
        body = MIMEText(conversation_text, "plain")
        msg.attach(body)

        raw_message_bytes = msg.as_bytes()
        raw_message_base64 = base64.urlsafe_b64encode(raw_message_bytes).decode("utf-8")

        message = {'raw': raw_message_base64}

        service.users().messages().send(userId=EMAIL_ADDRESS, body=message).execute()

        print("Email sent successfully!")
    except FileNotFoundError as e:
        print("Error: The credentials file was not found.")
    except google.auth.exceptions.DefaultCredentialsError as e:
        print("Error: Authentication failed. Check your credentials.")
    except Exception as e:
        print("Error sending email:", str(e))


# Function to test the collect_feedback function
def test_collect_feedback():
    with open('feedback.txt', 'w') as f:
        f.write('')


if __name__ == '__main__':
    print('PyCharm')
    say("Hello, I am Quantum")

    # Construct the LLAMA index from a directory of documents
    llama_index = construct_index("context_data/data")

    # Initialize the default command type to 'text'
    command_type = 't'

    while True:
        print("Waiting for your instructions....")

        # Print command options only if the command type is 'text'
        if command_type == 't':
            print("Type 't' for text command, 'v' for voice command, 'g' for Google search, "
                  "'o' for OpenAI knowledge base search, 'e' to send an email summary, or 'exit' to quit: ")

        command = input().strip().lower()

        if command == 'exit' or command == 'quit':
            print("Quantum: Goodbye!")
            say("Goodbye!")
            break
        elif command == 't':
            text_command = input("You can type your query here: ")
            chat_with_bot(llama_index, text_command, conversation_history)
        elif command == 'v':
            voice_query = takeCommand()
            if voice_query.strip():
                chat_with_bot(llama_index, voice_query, conversation_history)
        elif command == 'g':
            search_query = input("Enter your Google search query: ")
            results = google_search(search_query)
            for i, result in enumerate(results, start=1):
                print(f"{i}. {result}")
                say(f"{i}. {result}")
        elif command == 'o':
            openai_query = input("Enter your question: ")
            response = openai_search(openai_query)
            print(f"OpenAI Knowledge Base Response: {response}")
            say(f"OpenAI Knowledge Base Response: {response}")
        elif command == 'e':
            send_summary_email(conversation_history)
        elif command == 'set command type':
            new_command_type = input("Enter the new command type ('t', 'v', 'g', 'o', or 'e'): ").strip().lower()
            if new_command_type in ['t', 'v', 'g', 'o', 'e']:
                command_type = new_command_type
                print(f"Quantum: Command type set to '{command_type}'.")
            else:
                print("Quantum: Invalid command type. Please choose from 't', 'v', 'g', 'o', or 'e'.")
        else:
            print("Quantum: Sorry, I didn't understand that command.")
            say("Sorry, I didn't understand that command.")
