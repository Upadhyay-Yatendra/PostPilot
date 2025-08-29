from langchain.embeddings.openai import OpenAIEmbeddings
import numpy as np
from typing import List, Optional, Dict, Any

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings()

def get_embedding(text: str) -> List[float]:
    """
    Generate an embedding for the given text using OpenAI embeddings.
    """
    return embeddings.embed_query(text)

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Compute the cosine similarity between two vectors.
    """
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def most_similar_post(user_posts: List[Dict[str, Any]], prompt_embedding: List[float]) -> Optional[str]:
    """
    DEPRECATED: This function is now replaced by Pinecone vector search.
    Kept for backward compatibility.
    
    Find the most similar post to the given prompt embedding.
    Now generates embeddings on-the-fly instead of expecting pre-stored embeddings.

    Args:
        user_posts: A list of user post dictionaries (each must have "text").
        prompt_embedding: The embedding of the prompt to compare against.

    Returns:
        The text of the most similar post, or None if no valid posts are found.
    """
    max_sim = -1
    best_post = None

    print(f"[DEPRECATED] Analyzing {len(user_posts)} posts for style similarity...")
    print("Consider using PineconeService.find_similar_post() for better performance")

    for i, post in enumerate(user_posts):
        post_text = post.get("text")
        if not post_text or len(post_text.strip()) < 10:  # Skip very short posts
            continue

        try:
            # Generate embedding on-the-fly
            print(f"Generating embedding for post {i+1}...")
            post_embedding = get_embedding(post_text)
            
            # Calculate cosine similarity
            sim = cosine_similarity(post_embedding, prompt_embedding)
            print(f"Post {i+1} similarity: {sim:.3f}")
            
            if sim > max_sim:
                max_sim = sim
                best_post = post_text
                print(f"New best post found with similarity: {sim:.3f}")
                
        except Exception as e:
            print(f"Error generating embedding for post {i+1}: {e}")
            continue

    if best_post is None:
        print("No valid posts found for style matching")
        return None
    
    print(f"Best matching post found with similarity: {max_sim:.3f}")
    return best_post