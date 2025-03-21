"""
vector_store.py
Implements a local vector database for movie information using Chroma DB.
"""

import os
import json
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

class MovieVectorStore:
    """Manages a local vector database for movie information."""
    
    def __init__(self, db_directory: str = "db"):
        """
        Initialize the vector database.
        
        Parameters:
        - db_directory (str): Directory to store the database files
        """
        # Create database directory if it doesn't exist
        os.makedirs(db_directory, exist_ok=True)
        
        # Initialize Chroma client with persistent storage
        self.client = chromadb.PersistentClient(path=db_directory)
        
        # Use Sentence Transformers for embeddings (lightweight model)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"  # Small but effective embedding model
        )
        
        # Create or get the collection for movies
        self.collection = self.client.get_or_create_collection(
            name="movies",
            embedding_function=self.embedding_function
        )
    
    def add_movie(self, movie_info: Dict[str, Any]):
        """
        Add or update a movie in the vector database.
        
        Parameters:
        - movie_info (dict): Movie information from API
        """
        # Generate a unique ID based on title and year
        movie_id = f"{movie_info.get('title', 'unknown')}_{movie_info.get('year', '')}"
        movie_id = movie_id.lower().replace(' ', '_')
        
        # Create searchable text from movie info
        search_text = f"{movie_info.get('title', '')} ({movie_info.get('year', '')}). "
        search_text += f"Directed by {movie_info.get('director', '')}. "
        search_text += f"Starring {', '.join(movie_info.get('cast', [])[:3])}. "
        search_text += f"Genre: {movie_info.get('genre', '')}. "
        search_text += movie_info.get('description', '')
        
        # Add or update the document in the collection
        self.collection.upsert(
            ids=[movie_id],
            documents=[search_text],
            metadatas=[movie_info]
        )
        
        return movie_id
    
    def search_movies(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for movies using semantic similarity.
        
        Parameters:
        - query (str): The search query
        - n_results (int): Number of results to return
        
        Returns:
        - list: Matching movie information
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Process results
        movies = []
        if results and results['metadatas'] and results['metadatas'][0]:
            for metadata, distance in zip(results['metadatas'][0], results['distances'][0]):
                # Add relevance score (convert distance to similarity score)
                metadata['relevance_score'] = round((1 - distance) * 100, 2)  
                movies.append(metadata)
                
        return movies
    
    def get_recommendations(self, movie_title: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Get movie recommendations based on similarity to a given movie.
        
        Parameters:
        - movie_title (str): Title of the movie to get recommendations for
        - n_results (int): Number of recommendations to return
        
        Returns:
        - list: Similar movies
        """
        # First try to find the exact movie
        if len(self.collection.get(where={"title": movie_title})["ids"]) > 0:
            movie_id = self.collection.get(where={"title": movie_title})["ids"][0]
            
            # Get recommendations based on the movie's embedding
            results = self.collection.query(
                ids=[movie_id],
                n_results=n_results + 1  # +1 because the query movie will be included
            )
            
            # Process results, excluding the query movie
            movies = []
            if results and results['metadatas'] and results['metadatas'][0]:
                for i, (metadata, distance) in enumerate(zip(results['metadatas'][0], results['distances'][0])):
                    # Skip the first result if it's the query movie itself
                    if i == 0 and distance < 0.01:  # Almost identical
                        continue
                    
                    # Add relevance score
                    metadata['relevance_score'] = round((1 - distance) * 100, 2)
                    movies.append(metadata)
                    
            return movies
        else:
            # If movie not found, fall back to semantic search
            return self.search_movies(f"Movies similar to {movie_title}", n_results)
    
    def get_movie_count(self) -> int:
        """
        Get the number of movies in the database.
        
        Returns:
        - int: Number of movies
        """
        return self.collection.count()
