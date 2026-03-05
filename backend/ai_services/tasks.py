
from celery import shared_task
import time
import os
from knowledge.models import KnowledgeFile, KnowledgeChunk
from .utils import extract_text_from_file, split_text
import google.generativeai as genai
from monitoring.utils import Logger
from django.contrib.postgres.search import SearchVector
from django.db import transaction

@shared_task
def add(x, y):
    time.sleep(1) # Simulate delay
    return x + y

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def process_knowledge_file(self, file_id):
    try:
        Logger.info('KNOWLEDGE', f"Processing knowledge file {file_id}...")
        try:
            knowledge_file = KnowledgeFile.objects.get(id=file_id)
        except KnowledgeFile.DoesNotExist:
            Logger.error('KNOWLEDGE', f"KnowledgeFile with id {file_id} not found.")
            return "File not found"

        # Update status to processing
        knowledge_file.status = 'processing'
        knowledge_file.processing_error = None
        knowledge_file.save()
        
        if not knowledge_file.file:
            error_msg = "No file associated with this KnowledgeFile object."
            Logger.error('KNOWLEDGE', error_msg)
            knowledge_file.status = 'failed'
            knowledge_file.processing_error = error_msg
            knowledge_file.save()
            return "No file"
            
        file_path = knowledge_file.file.path
        Logger.info('KNOWLEDGE', f"Extracting text from {file_path}...")
        
        text = extract_text_from_file(file_path)
        
        if not text:
            error_msg = "No text extracted or empty file."
            Logger.error('KNOWLEDGE', error_msg)
            knowledge_file.status = 'failed'
            knowledge_file.processing_error = error_msg
            knowledge_file.save()
            return "No text extracted"
            
        Logger.info('KNOWLEDGE', "Splitting text into chunks (approx 700 tokens)...")
        # Approx 700 tokens * 4 chars/token = 2800 chars. Overlap 100 tokens * 4 = 400 chars.
        chunks = split_text(text, chunk_size=2800, chunk_overlap=400)
        chunk_count = len(chunks)
        Logger.info('KNOWLEDGE', f"Generated {chunk_count} chunks for file {file_id}")
        
        Logger.info('KNOWLEDGE', "Storing text chunks for immediate preview...")
        
        # Delete existing chunks for this file to avoid duplicates on re-processing
        KnowledgeChunk.objects.filter(knowledge_file=knowledge_file).delete()
        
        # 1. Bulk Create all chunks with embedding=None first
        chunks_to_create = []
        for i, chunk_text in enumerate(chunks):
            chunks_to_create.append(KnowledgeChunk(
                chatbot=knowledge_file.chatbot,
                knowledge_file=knowledge_file,
                content=chunk_text,
                chunk_index=i,
                embedding=None
            ))
            
        created_chunk_objects = KnowledgeChunk.objects.bulk_create(chunks_to_create)
        Logger.info('KNOWLEDGE', f"Stored {len(created_chunk_objects)} chunks. Populating search vectors...")

        # Populate search_vector for hybrid search
        try:
            with transaction.atomic():
                KnowledgeChunk.objects.filter(knowledge_file=knowledge_file).update(search_vector=SearchVector('content'))
        except Exception as e:
            Logger.warning('KNOWLEDGE', f"Failed to populate search_vector (likely SQLite): {e}")

        Logger.info('KNOWLEDGE', "Starting embedding generation...")
        
        # 2. Update KnowledgeFile status to indicate embedding phase (optional, or just keep 'processing')
        # We can also update chunk_count now
        knowledge_file.chunk_count = len(chunks)
        knowledge_file.save()

        # Initialize Gemini client
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
             warn_msg = "Gemini API key missing. Skipping embedding generation."
             Logger.warning('KNOWLEDGE', warn_msg)
             # We do NOT fail here, we just skip embeddings so preview still works.
             knowledge_file.status = 'completed'
             knowledge_file.processing_error = "Completed without embeddings (No Gemini Key)"
             knowledge_file.save()
             return "Processed chunks (No Embeddings)"

        genai.configure(api_key=api_key)
        
        # 3. Iterate and update with embeddings
        batch_size = 10
        total_chunks = len(chunks)
        
        # We need to map chunks back to their objects to update them.
        # created_chunk_objects has the correct order.
        
        for i in range(0, total_chunks, batch_size):
            batch_objects = created_chunk_objects[i:i + batch_size]
            
            try:
                # Generate embeddings for each chunk in the batch
                for obj in batch_objects:
                    try:
                        result = genai.embed_content(
                            model="models/gemini-embedding-001",
                            content=obj.content,
                            task_type="retrieval_document",
                            output_dimensionality=768
                        )
                        obj.embedding = result['embedding']
                    except Exception as e:
                        Logger.error('KNOWLEDGE', f"Error generating Gemini embedding for chunk {obj.id}: {e}")
                        # We can continue or fail. Let's continue and leave embedding as None if it fails.
                        obj.embedding = None

                # Bulk update the embeddings for this batch
                KnowledgeChunk.objects.bulk_update(batch_objects, ['embedding'])
                
            except Exception as e:
                Logger.error('KNOWLEDGE', f"Error updating batch {i}: {e}")
                raise e

        # Update status to completed
        knowledge_file.status = 'completed'
        knowledge_file.save()
        
        Logger.info('KNOWLEDGE', f"Successfully processed {total_chunks} chunks for file {file_id}")
        return f"Processed {total_chunks} chunks"
        
    except Exception as e:
        Logger.error('KNOWLEDGE', f"Error processing file: {e}")
        # Update status to failed
        if 'knowledge_file' in locals():
            knowledge_file.status = 'failed'
            knowledge_file.processing_error = str(e)
            knowledge_file.save()
        raise e
        # Re-raise to let Celery handle retry/failure if needed
        # raise e # Optional: if we want Celery to mark it as failed task too. 
        # Since we handle the status in DB, maybe we don't strictly need to raise, 
        # but it's good practice for monitoring.
        return f"Failed: {str(e)}"
