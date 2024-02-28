# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 10:03:59 2024

@author: DELL
"""
from flask import Flask, render_template, request
import nltk
import PyPDF2
import difflib

# Download the Punkt tokenizer for sentence splitting
nltk.download('punkt')

app = Flask(__name__)

user_data = {}  # Store user-specific data

# Define mapping between sections and PDF paths
section_pdfs = {
    'know about company': "..\\welchat\\about_company.pdf",
    'know more about fund': "..\\welchat\\WOLP Fund 2_FAQs_vf-UPDATED.pdf",
    'know more about safety to quality protocol': "..\\welchat\\Safety and quality protocols faqs.pdf",
    'contact us': "..\\welchat\\contact_us.pdf",
    # 'XXXX': "C:\\path\\to\\xxxx.pdf"
}

section_info = {
    'know about company' : 'Find out what the company does and insights',
    'know more about fund': 'Learn about our investment funds and frequently asked questions.',
    'know more about safety to quality protocol': 'Understand our safety and quality protocols.',
    'contact us': 'Get our contact details'
    # Add descriptions for other sections as needed
}

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    return text

def extract_questions_and_answers(pdf_text):
    sentences = nltk.sent_tokenize(pdf_text)
    qa_pairs = []

    i = 0
    while i < len(sentences):
        if sentences[i].endswith('?'):
            question = sentences[i]
            answer = ""
            i += 1
            while i < len(sentences) and not sentences[i].endswith('?'):
                answer += sentences[i] + ' '
                i += 1
            qa_pairs.append((question, answer.strip()))
        else:
            i += 1
    
    return qa_pairs

def find_best_match(user_input, questions):
    user_tokens = nltk.word_tokenize(user_input.lower())
    best_match = None
    max_similarity = 0

    for question in questions:
        question_tokens = nltk.word_tokenize(question[0].lower())
        similarity = difflib.SequenceMatcher(None, user_tokens, question_tokens).ratio()

        if similarity > max_similarity:
            max_similarity = similarity
            best_match = question

    return best_match

@app.route('/')
def index():
    return render_template('index1.html')

@app.route('/start', methods=['POST'])
def start():
    username = request.form['username']
    user_data['username'] = username
    return render_template('sections.html', sections=section_pdfs.keys(), username=username, section_info=section_info)

@app.route('/chat/<section>', methods=['GET', 'POST'])
def chat(section):
    username = user_data.get('username', 'Guest')
    pdf_path = section_pdfs.get(section, '')

    if not pdf_path:
        return "Invalid section."

    pdf_text = extract_text_from_pdf(pdf_path)
    qa_pairs = extract_questions_and_answers(pdf_text)

    previous_responses = user_data.get('previous_responses', [])

    if request.method == 'POST':
        user_input = request.form['user_input']
        if user_input.lower() == 'bye':
            return render_template('bye.html', username=username)

        best_match = find_best_match(user_input, qa_pairs)
        response = best_match[1] if best_match else "I'm sorry, I couldn't understand that."

        # Append user and bot messages to a list
        user_message = f'You: {user_input}'
        bot_message = f'Bot: {response}'

        # Store the previous responses
        previous_responses.append({'class': 'user-message', 'content': user_message})
        previous_responses.append({'class': 'bot-message', 'content': bot_message})
        user_data['previous_responses'] = previous_responses

        return render_template('chat.html', username=username, section=section, messages=[{'class': 'user-message', 'content': user_message}, {'class': 'bot-message', 'content': bot_message}], sample_questions=qa_pairs[:5], previous_responses=previous_responses)

    return render_template('chat.html', username=username, section=section, sample_questions=qa_pairs[:5], previous_responses=previous_responses)

if __name__ == '__main__':
    app.run()

