import streamlit as st
import spacy
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import docx
import os
import pyttsx3

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_GENAI_API_KEY")

# Initialize SpaCy model
nlp = spacy.load("en_core_web_sm")

# Initialize Google Generative AI
google_llm = GoogleGenerativeAI(model="models/gemini-1.5-flash", google_api_key=api_key)

# Define the prompt template for discussion format
google_prompt = PromptTemplate(
    input_variables=["text"],
    template="Convert the following text into a discussion between two people, like a podcast:in which there are two members one is named chutki who is the host and other is bheem who is the guest with no extra text and in format Chutki: , Bheem: without any next line \n{text}"
)

# Create a Google discussion generation chain
google_discussion_chain = LLMChain(llm=google_llm, prompt=google_prompt)

# Function to extract text from uploaded documents
def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        pdf_reader = PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    elif uploaded_file.name.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    else:
        return None

# Function to convert text to speech
def text_to_speech(discussion_text):
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")

    # Find available voices (try to identify male/female)
    female_voice = None
    male_voice = None
    
    # Try to find appropriate voices
    for voice in voices:
        if "female" in voice.name.lower():
            female_voice = voice.id
        elif "male" in voice.name.lower():
            male_voice = voice.id

    # Fallback to first two voices if specific genders not found
    if not female_voice:
        female_voice = voices[1].id
    if not male_voice:
        male_voice = voices[0].id if len(voices) > 1 else voices[0].id

    # Split discussion into lines
    lines = discussion_text.split("\n")
    
    # Process each line individually
    for line in lines:
        if not line.strip():
            continue
            
        # Split speaker and dialogue
        if ": " in line:
            speaker, dialogue = line.split(": ", 1)
        else:
            continue  # Skip malformed lines

        # Set voice based on speaker
        if "Chutki" in speaker:
            engine.setProperty("voice", female_voice)
        elif "Bheem" in speaker:
            engine.setProperty("voice", male_voice)
        else:
            continue  # Skip unknown speakers

        # Speak the dialogue text without the speaker name
        engine.say(dialogue)
        engine.runAndWait()  # Ensure full speech before continuing


# Streamlit app layout
st.title("Podcast Style Discussion Generator")
st.write(
    """
    Welcome to Dholakpur Podcast! This app allows you to input text manually or upload documents (PDF/DOCX) to convert the content into a podcast-style discussion.
    """
)

# Text input or file upload
st.subheader("Input Method")
input_method = st.radio("Choose your input method:", ["Text Box", "Upload Document"])

text = ""
if input_method == "Text Box":
    text = st.text_area("Enter the text to convert", height=200)
elif input_method == "Upload Document":
    uploaded_file = st.file_uploader("Upload a PDF or DOCX file", type=["pdf", "docx"])
    if uploaded_file:
        with st.spinner("Extracting text from the document..."):
            text = extract_text_from_file(uploaded_file)
        if text:
            st.success("Text extracted from the document!")
        else:
            st.error("Unable to extract text. Please upload a valid PDF or DOCX file.")

# Generate discussion
if st.button("Generate Discussion"):
    if text.strip():
        with st.spinner("Generating discussion..."):
            discussion = google_discussion_chain.run(text=text)
        st.success("Discussion generated!")
        st.subheader("Podcast Style Discussion")
        st.write(discussion)

        # Convert to speech
        with st.spinner("Generating audio..."):
            text_to_speech(discussion)
        st.success("Audio generated! 🎙️")

    else:
        st.error("Please enter text or upload a document to generate a discussion.")


