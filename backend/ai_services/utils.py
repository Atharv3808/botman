
import os
import backoff
import fitz  # PyMuPDF
from openai import OpenAI
from google import genai
from google.genai import errors
from pgvector.django import CosineDistance
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import connection
from knowledge.models import KnowledgeChunk
import numpy as np

from monitoring.utils import Logger
from cryptography.fernet import Fernet
import base64
from django.conf import settings

def get_cipher():
    """Returns a Fernet cipher using the Django SECRET_KEY."""
    # Fernet requires a 32-byte url-safe base64-encoded key
    # We'll pad or truncate the SECRET_KEY to get exactly 32 bytes
    key = settings.SECRET_KEY.encode()
    if len(key) < 32:
        key = key.ljust(32, b'0')
    else:
        key = key[:32]
    return Fernet(base64.urlsafe_b64encode(key))

def encrypt_data(data):
    """Encrypts string data."""
    if not data:
        return None
    cipher = get_cipher()
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    """Decrypts string data."""
    if not encrypted_data:
        return None
    cipher = get_cipher()
    try:
        return cipher.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        Logger.error('ENCRYPTION', f"Decryption failed: {e}")
        return None

def extract_text_from_file(file_path):
    """
    Extracts text from a file (PDF or TXT) using high-performance PyMuPDF for PDFs.
    """
    ext = os.path.splitext(file_path)[1].lower()
    text_parts = []
    
    try:
        if ext == '.pdf':
            # Use PyMuPDF (fitz) for much faster text extraction
            with fitz.open(file_path) as doc:
                for page in doc:
                    extracted = page.get_text()
                    if extracted:
                        text_parts.append(extracted)
            return "\n".join(text_parts)
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    except Exception as e:
        Logger.error('EMBEDDING', f"Error extracting text from {file_path}: {e}")
        return ""

def split_text(text, chunk_size=1000, chunk_overlap=200):
    """
    Splits text into chunks of specified size with overlap.
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]
        chunks.append(chunk)
        
        # If we reached the end, break
        if end == text_len:
            break
            
        # Move start forward by chunk_size - overlap
        # Ensure we always move forward at least 1 char to avoid infinite loop if overlap >= size
        step = max(1, chunk_size - chunk_overlap)
        start += step
        
    return chunks

def embed_text(text, task_type="retrieval_query"):
    """
    Generates embedding for a given text using Gemini (gemini-embedding-001).
    Includes exponential backoff for rate limits.
    """
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        Logger.warning('EMBEDDING', "Gemini API key is missing.")
        return None
        
    client = genai.Client(api_key=api_key)

    @backoff.on_exception(
        backoff.expo,
        (errors.ClientError),
        max_tries=5, # Higher tries for embeddings as they are often batch processed
        giveup=lambda e: getattr(e, 'code', None) != 429
    )
    def _execute_embed():
        return client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=text,
            config={
                'task_type': task_type,
                'output_dimensionality': 768
            }
        )

    try:
        result = _execute_embed()
        return result.embeddings[0].values
    except Exception as e:
        Logger.error('EMBEDDING', f"Error generating Gemini embedding: {e}")
        return None

def search_knowledge(chatbot, embedding, query_text=None, limit=5, threshold=0.45):
    """
    Searches for relevant knowledge chunks for a chatbot using Hybrid Search (Vector + Keyword).
    Uses Reciprocal Rank Fusion (RRF) to combine results.
    
    Args:
        chatbot: Chatbot instance
        embedding: Vector embedding of the query
        query_text: Original text query (required for keyword search)
        limit: Number of chunks to return
        threshold: Similarity threshold for vector search (0-1)
    """
    if not embedding:
        Logger.warning('RAG_SEARCH', f"No embedding provided for Bot {chatbot.id}")
        return []
        
    Logger.info('RAG_SEARCH', f"Searching knowledge for Bot {chatbot.id} (limit={limit}, threshold={threshold}, hybrid={bool(query_text)})")
    
    # --- 1. Semantic Search (Vector) ---
    vector_chunks = []
    try:
        if connection.vendor != 'sqlite':
            # Try DB-level search first (Postgres optimized)
            vector_chunks = list(KnowledgeChunk.objects.filter(chatbot=chatbot).annotate(
                distance=CosineDistance('embedding', embedding)
            ).order_by('distance')[:limit*2])
        else:
            raise Exception("SQLite cannot perform vector search, skipping to Python fallback.")
        
    except Exception as e:
        Logger.info('RAG_SEARCH', f"{e}")
        try:
            # Fallback to Python-level search using numpy
            all_chunks = KnowledgeChunk.objects.filter(chatbot=chatbot, embedding__isnull=False)
            
            query_emb = np.array(embedding)
            query_norm = np.linalg.norm(query_emb)
            
            scored_chunks = []
            for chunk in all_chunks:
                if chunk.embedding is None: continue
                
                chunk_emb = chunk.embedding 
                if not isinstance(chunk_emb, np.ndarray):
                    chunk_emb = np.array(chunk_emb)
                    
                chunk_norm = np.linalg.norm(chunk_emb)
                
                if chunk_norm == 0 or query_norm == 0:
                    similarity = 0
                else:
                    similarity = np.dot(query_emb, chunk_emb) / (query_norm * chunk_norm)
                
                # Ensure similarity is within [-1, 1]
                similarity = min(max(similarity, -1.0), 1.0)
                
                chunk.distance = 1.0 - similarity
                scored_chunks.append(chunk)
                
            # Sort by distance (ascending)
            scored_chunks.sort(key=lambda x: x.distance)
            vector_chunks = scored_chunks[:limit*2]
            
        except Exception as ex:
            Logger.error('RAG_SEARCH', f"Python vector search failed: {ex}")
            vector_chunks = []

    # Filter vector chunks by threshold
    max_distance = 1 - threshold
    qualified_vector_chunks = []
    for chunk in vector_chunks:
        if not hasattr(chunk, 'distance') or chunk.distance is None:
            continue
        if chunk.distance <= max_distance:
            qualified_vector_chunks.append(chunk)

    # If no query text provided, return semantic results only
    if not query_text:
        return qualified_vector_chunks[:limit]

    # --- 2. Keyword Search (BM25) ---
    keyword_chunks = []
    if connection.vendor != 'sqlite':
        try:
            # Simple English search
            search_query = SearchQuery(query_text, config='english')
            keyword_chunks = list(KnowledgeChunk.objects.filter(
                chatbot=chatbot,
                search_vector=search_query
            ).annotate(
                rank=SearchRank('search_vector', search_query)
            ).order_by('-rank')[:limit*2])
            
            Logger.info('RAG_SEARCH', f"Keyword search found {len(keyword_chunks)} chunks")
            
        except Exception as e:
            Logger.warning('RAG_SEARCH', f"Keyword search failed (likely not Postgres): {e}")
            keyword_chunks = []
    else:
        # SQLite doesn't support SearchQuery out of the box natively with Django ORM matching
        keyword_chunks = list(KnowledgeChunk.objects.filter(chatbot=chatbot, content__icontains=query_text)[:limit*2])
        Logger.info('RAG_SEARCH', f"SQLite Keyword fallback found {len(keyword_chunks)} chunks")

    # --- 3. Reciprocal Rank Fusion (RRF) ---
    # Combine results
    # RRF Score = 1 / (k + rank)
    k = 60
    chunk_scores = {}
    
    # Process Vector Results
    for rank, chunk in enumerate(qualified_vector_chunks):
        chunk_id = chunk.id
        if chunk_id not in chunk_scores:
            chunk_scores[chunk_id] = {'chunk': chunk, 'score': 0.0}
        
        # Add vector score
        chunk_scores[chunk_id]['score'] += 1.0 / (k + rank + 1)

    # Process Keyword Results
    for rank, chunk in enumerate(keyword_chunks):
        chunk_id = chunk.id
        if chunk_id not in chunk_scores:
            # We need to fetch the chunk if it wasn't in vector results
            # But wait, 'chunk' here is the object, so we have it.
            # However, if it wasn't in vector results, it might not have 'distance' attribute.
            # We should probably calculate distance if possible, or just treat it as valid.
            chunk.distance = 0.0 # Dummy distance for compatibility if needed
            chunk_scores[chunk_id] = {'chunk': chunk, 'score': 0.0}
        
        # Add keyword score
        chunk_scores[chunk_id]['score'] += 1.0 / (k + rank + 1)
    
    # Sort by RRF score
    sorted_chunks = sorted(chunk_scores.values(), key=lambda x: x['score'], reverse=True)
    
    final_chunks = []
    for item in sorted_chunks[:limit]:
        chunk = item['chunk']
        chunk.combined_score = item['score'] # Attach score for debugging/logging
        final_chunks.append(chunk)
        
    Logger.info('RAG_SEARCH', f"Hybrid search returned {len(final_chunks)} chunks")
    return final_chunks
