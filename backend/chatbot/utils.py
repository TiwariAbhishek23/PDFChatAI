import fitz
import os
import openai
import tiktoken
from django.db import connection
from .models import Document


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file."""
    text = ""
    with fitz.open(pdf_file) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text.strip()

def get_embedding(text, model="text-embedding-ada-002"):
    """Generate an embedding for the given text using OpenAI API."""
    openai.api_key = OPENAI_API_KEY
    response = openai.Embedding.create(input=text, model=model)
    return response['data'][0]['embedding']

def chunk_text(text, chunk_size=500):
    """Split text into smaller chunks for embedding generation."""
    encoding = tiktoken.encoding_for_model("text-embedding-ada-002")
    tokens = encoding.encode(text)

    chunks = []
    for i in range(0, len(tokens), chunk_size):
        chunk_tokens = tokens[i:i+chunk_size]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
    return chunks

def find_relevant_documents(query_embedding, top_k=3):
    """Find the top-k most similar document chunks in the vector database."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, extracted_text, 1 - (embedding <=> %s) AS similarity
            FROM chatbot_document
            ORDER BY similarity DESC
            LIMIT %s;
        """, [query_embedding, top_k])

        results = cursor.fetchall()
    
    return [{"id": row[0], "text": row[1], "similarity": row[2]} for row in results]

def generate_augmented_response(user_query, retrieved_docs):
    """Generate a response using OpenAI, augmenting it with retrieved document text."""
    openai.api_key = OPENAI_API_KEY

    context = "\n\n".join([doc["text"] for doc in retrieved_docs])
    
    prompt = f"""You are an AI assistant answering questions based on provided documents. 
    Use the following document excerpts to answer the question: 

    {context}

    Question: {user_query}
    Answer:
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}]
    )

    return response["choices"][0]["message"]["content"]