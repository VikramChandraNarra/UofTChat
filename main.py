import requests
from bs4 import BeautifulSoup
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import faiss
import numpy as np
from flask import Flask, request, jsonify

# Step 1: Fetch and parse the webpage (this part is adapted from your original script)
url = "https://artsci.calendar.utoronto.ca/section/Computer-Science"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Step 2: Extract relevant data (headings and paragraphs)
data = []
current_heading = None
paragraphs = []

for elem in soup.find_all(['h1', 'h2', 'h3', 'p', 'div', 'li']):
    if elem.name in ['h1', 'h2', 'h3']:  # These are section headings
        if current_heading and paragraphs:
            data.append({
                "heading": current_heading,
                "paragraphs": ' '.join(paragraphs)
            })
            paragraphs = []
        current_heading = elem.get_text(strip=True)
    elif elem.name == 'p' or elem.name == 'li':
        paragraph = ' '.join(elem.stripped_strings)
        if paragraph:
            paragraphs.append(paragraph)

# Add the last section if needed
if current_heading and paragraphs:
    data.append({
        "heading": current_heading,
        "paragraphs": ' '.join(paragraphs)
    })

# Step 3: Save data as a DataFrame (could be loaded from a CSV/JSON directly too)
df = pd.DataFrame(data)

# Step 4: Initialize the SentenceTransformer model for embedding
model = SentenceTransformer('all-MiniLM-L6-v2')

# Step 5: Create embeddings for the paragraphs
corpus = df['paragraphs'].tolist()
corpus_embeddings = model.encode(corpus, convert_to_tensor=False)

# Step 6: Use FAISS to index these embeddings for efficient searching
embedding_dim = corpus_embeddings.shape[1]
index = faiss.IndexFlatL2(embedding_dim)
index.add(np.array(corpus_embeddings))

# Step 7: Define a function to get the best response to a user query
def get_best_response(query):
    query_embedding = model.encode(query, convert_to_tensor=False)
    query_embedding = np.array(query_embedding).reshape(1, -1)

    # Search FAISS index for the most similar paragraph
    D, I = index.search(query_embedding, k=1)  # Get top-1 result
    best_match_idx = I[0][0]
    best_response = df.iloc[best_match_idx]['paragraphs']
    return best_response

# Step 8: Set up the Flask web application
app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get('query')
    
    if not user_input:
        return jsonify({"error": "No query provided"}), 400
    
    # Get the best response based on the query
    response = get_best_response(user_input)
    return jsonify({"response": response})

# Step 9: Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
