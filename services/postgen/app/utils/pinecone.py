from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any, Optional
import uuid
import time
from app.config import PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME
from app.utils.embeddings import get_embedding

class PineconeService:
    def __init__(self):
        self.pc = None
        self.index = None
        self.initialize_pinecone()
    
    def initialize_pinecone(self):
        """Initialize Pinecone connection and index"""
        try:
            # New way to connect
            self.pc = Pinecone(api_key=PINECONE_API_KEY)

            # List existing indexes
            existing_indexes = [i["name"] for i in self.pc.list_indexes()]

            # Create index if it doesn't exist
            if PINECONE_INDEX_NAME not in existing_indexes:
                print(f"Creating Pinecone index: {PINECONE_INDEX_NAME}")
                self.pc.create_index(
                    name=PINECONE_INDEX_NAME,
                    dimension=1536,  # OpenAI embedding dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",      # adjust if needed
                        region=PINECONE_ENVIRONMENT  # make sure this matches your .env
                    ),
                )
                # Wait for index to be ready
                while PINECONE_INDEX_NAME not in [
                    i["name"] for i in self.pc.list_indexes()
                ]:
                    time.sleep(1)

            self.index = self.pc.Index(PINECONE_INDEX_NAME)
            print(f"Connected to Pinecone index: {PINECONE_INDEX_NAME}")
            
        except Exception as e:
            print(f"Error initializing Pinecone: {e}")
            raise

    def store_user_posts(self, username: str, posts: List[Dict[str, Any]]) -> bool:
        """Store user's posts in Pinecone with embeddings"""
        try:
            vectors_to_upsert = []
            
            for post in posts:
                # Get the post content (adjust field names based on your data structure)
                post_content = post.get("content", "") or post.get("text", "") or post.get("post_text", "")
                
                if not post_content or len(post_content.strip()) < 10:
                    continue  # Skip very short or empty posts
                
                # Generate embedding for the post
                embedding = get_embedding(post_content)
                if not embedding:
                    print(f"Failed to generate embedding for post: {post_content[:50]}...")
                    continue
                
                # Create unique ID for this post
                post_id = f"{username}_{post.get('post_id', str(uuid.uuid4()))}"
                
                # Prepare metadata
                metadata = {
                    "username": username,
                    "content": post_content[:1000],  # Limit content length for metadata
                    "post_id": post.get("post_id", ""),
                    "scraped_at": post.get("scraped_at", ""),
                    "likes": post.get("likes", 0),
                    "comments": post.get("comments", 0),
                    "reposts": post.get("reposts", 0)
                }
                
                vectors_to_upsert.append({
                    "id": post_id,
                    "values": embedding,
                    "metadata": metadata
                })
            
            if vectors_to_upsert:
                # Upsert in batches of 100
                batch_size = 100
                for i in range(0, len(vectors_to_upsert), batch_size):
                    batch = vectors_to_upsert[i:i + batch_size]
                    self.index.upsert(vectors=batch)
                    print(f"Upserted batch {i//batch_size + 1} with {len(batch)} vectors")
                
                print(f"Successfully stored {len(vectors_to_upsert)} posts for {username}")
                return True
            else:
                print(f"No valid posts to store for {username}")
                return False
                
        except Exception as e:
            print(f"Error storing posts for {username}: {e}")
            return False

    def find_similar_post(self, username: str, query: str, top_k: int = 1) -> Optional[str]:
        """Find similar posts by a specific user based on query"""
        try:
            # Generate embedding for the query
            query_embedding = get_embedding(query)
            if not query_embedding:
                print("Failed to generate embedding for query")
                return None
            
            # Search for similar posts by this specific user
            results = self.index.query(
                vector=query_embedding,
                filter={"username": username},
                top_k=top_k,
                include_metadata=True
            )
            
            if results.matches:
                # Return the content of the most similar post
                best_match = results.matches[0]
                content = best_match.metadata.get("content", "")
                print(f"Found similar post with score {best_match.score:.3f}")
                return content
            else:
                print(f"No similar posts found for user {username}")
                return None
                
        except Exception as e:
            print(f"Error finding similar post: {e}")
            return None

    def search_similar_posts(self, query: str, username: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar posts across all users or for a specific user"""
        try:
            query_embedding = get_embedding(query)
            if not query_embedding:
                return []
            
            # Build filter
            filter_dict = {}
            if username:
                filter_dict["username"] = username
            
            results = self.index.query(
                vector=query_embedding,
                filter=filter_dict if filter_dict else None,
                top_k=top_k,
                include_metadata=True
            )
            
            similar_posts = []
            for match in results.matches:
                similar_posts.append({
                    "content": match.metadata.get("content", ""),
                    "username": match.metadata.get("username", ""),
                    "score": match.score,
                    "post_id": match.metadata.get("post_id", ""),
                    "likes": match.metadata.get("likes", 0),
                    "comments": match.metadata.get("comments", 0)
                })
            
            return similar_posts
            
        except Exception as e:
            print(f"Error searching similar posts: {e}")
            return []

    def delete_user_posts(self, username: str) -> bool:
        """Delete all posts for a specific user"""
        try:
            # First, get all post IDs for this user
            query_response = self.index.query(
                vector=[0.0] * 1536,  # Dummy vector
                filter={"username": username},
                top_k=10000,  # Large number to get all posts
                include_metadata=True
            )
            
            if query_response.matches:
                post_ids = [match.id for match in query_response.matches]
                
                # Delete in batches
                batch_size = 1000
                for i in range(0, len(post_ids), batch_size):
                    batch = post_ids[i:i + batch_size]
                    self.index.delete(ids=batch)
                
                print(f"Deleted {len(post_ids)} posts for user {username}")
                return True
            else:
                print(f"No posts found to delete for user {username}")
                return True
                
        except Exception as e:
            print(f"Error deleting posts for {username}: {e}")
            return False

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the Pinecone index"""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": dict(stats.namespaces) if stats.namespaces else {}
            }
        except Exception as e:
            print(f"Error getting index stats: {e}")
            return {}

    def update_user_posts(self, username: str, new_posts: List[Dict[str, Any]]) -> bool:
        """Update posts for a user (delete old ones and add new ones)"""
        try:
            # Delete existing posts
            self.delete_user_posts(username)
            
            # Add new posts
            return self.store_user_posts(username, new_posts)
            
        except Exception as e:
            print(f"Error updating posts for {username}: {e}")
            return False

# Create the global instance
pinecone_service = PineconeService()