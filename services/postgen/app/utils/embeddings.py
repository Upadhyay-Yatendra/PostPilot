from langchain.embeddings.openai import OpenAIEmbeddings
import numpy as np
from typing import List, Optional

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
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def most_similar_post(user_posts: List, prompt_embedding: List[float]) -> Optional[str]:
    """
    Find the most similar post to the given prompt embedding.

    Args:
        user_posts: A list of user posts, each with an `embedding` attribute (comma-separated string).
        prompt_embedding: The embedding of the prompt to compare against.

    Returns:
        The text of the most similar post, or None if no valid posts are found.
    """
    max_sim = -1
    best_post = None

    for post in user_posts:
        if not post.embedding:
            continue
        try:
            # Convert the embedding string to a list of floats
            emb = [float(x) for x in post.embedding.split(",")]
        except ValueError:
            # Skip posts with invalid embeddings
            continue

        # Calculate cosine similarity
        sim = cosine_similarity(emb, prompt_embedding)
        if sim > max_sim:
            max_sim = sim
            best_post = post.text

    if best_post is None:
        raise ValueError("No valid posts with embeddings found.")
    
    return best_post