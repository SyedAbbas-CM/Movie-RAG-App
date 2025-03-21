"""
search_tools.py
Implements search tools for movie information and trailers using official APIs.
"""

import requests
import json
from urllib.parse import quote_plus
from typing import Dict, List, Any, Optional
from googleapiclient.discovery import build

class OMDbMovieSearchTool:
    """Tool for searching movie information using the OMDb API."""
    
    def __init__(self, api_key: str):
        """
        Initialize with OMDb API key.
        
        Parameters:
        - api_key (str): OMDb API key
        """
        self.api_key = api_key
    
    def search(self, query: str) -> Dict[str, Any]:
        """
        Search for movie information using the OMDb API.
        
        Parameters:
        - query (str): The movie title to search for
        
        Returns:
        - dict: Movie information results
        """
        try:
            # Make request to OMDb API
            url = f"http://www.omdbapi.com/?apikey={self.api_key}&t={quote_plus(query)}&plot=full"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return {"error": f"OMDb API request failed: {response.status_code}"}
            
            data = response.json()
            
            if data.get("Response") == "False":
                return {"error": data.get("Error", "Movie not found")}
            
            # Map OMDb response to our format
            movie_info = {
                "title": data.get("Title", query),
                "release_date": data.get("Released", ""),
                "director": data.get("Director", ""),
                "cast": data.get("Actors", "").split(", "),
                "rating": f"{data.get('imdbRating', '')}/10",
                "description": data.get("Plot", ""),
                "genre": data.get("Genre", ""),
                "poster": data.get("Poster", ""),
                "year": data.get("Year", ""),
                "runtime": data.get("Runtime", ""),
                "awards": data.get("Awards", "")
            }
            
            return {
                "raw_results": data,
                "structured_info": movie_info
            }
            
        except Exception as e:
            return {"error": f"OMDb search failed: {str(e)}"}


class YouTubeSearchTool:
    """Tool for searching YouTube videos using the official API."""
    
    def __init__(self, api_key: str):
        """
        Initialize with YouTube Data API key.
        
        Parameters:
        - api_key (str): YouTube Data API key
        """
        self.api_key = api_key
        # Lazy initialization of YouTube service
        self._youtube = None
    
    @property
    def youtube(self):
        """Lazy initialization of YouTube API client."""
        if self._youtube is None:
            self._youtube = build('youtube', 'v3', developerKey=self.api_key)
        return self._youtube
    
    def search(self, query: str) -> List[Dict[str, str]]:
        """
        Search for YouTube videos related to movies using the official API.
        
        Parameters:
        - query (str): The search query
        
        Returns:
        - list: YouTube video results
        """
        try:
            # Add "trailer official" to make the search more specific for movie trailers
            search_query = f"{query} trailer official"
            
            # Call the YouTube API search.list method
            search_response = self.youtube.search().list(
                q=search_query,
                part='snippet',
                maxResults=3,
                type='video'
            ).execute()
            
            results = []
            for item in search_response.get('items', []):
                video_id = item['id']['videoId']
                video_title = item['snippet']['title']
                thumbnail = item['snippet']['thumbnails']['high']['url']
                channel_title = item['snippet']['channelTitle']
                published_at = item['snippet']['publishedAt']
                
                results.append({
                    "title": video_title,
                    "link": f"https://youtube.com/watch?v={video_id}",
                    "video_id": video_id,
                    "thumbnail": thumbnail,
                    "channel": channel_title,
                    "published_at": published_at
                })
            
            return results
            
        except Exception as e:
            return [{"error": f"YouTube API search failed: {str(e)}"}]


class TMDBMovieSearchTool:
    """Tool for searching movie information using The Movie Database (TMDB) API."""
    
    def __init__(self, api_key: str):
        """
        Initialize with TMDB API key.
        
        Parameters:
        - api_key (str): TMDB API key
        """
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
    
    def search(self, query: str) -> Dict[str, Any]:
        """
        Search for movie information using the TMDB API.
        
        Parameters:
        - query (str): The movie title to search for
        
        Returns:
        - dict: Movie information results
        """
        try:
            # Search for the movie
            search_url = f"{self.base_url}/search/movie?api_key={self.api_key}&query={quote_plus(query)}"
            search_response = requests.get(search_url, timeout=10)
            
            if search_response.status_code != 200:
                return {"error": f"TMDB API search request failed: {search_response.status_code}"}
            
            search_data = search_response.json()
            
            if not search_data.get("results"):
                return {"error": "Movie not found"}
            
            # Get the first result (most relevant)
            movie_id = search_data["results"][0]["id"]
            
            # Get detailed movie information
            details_url = f"{self.base_url}/movie/{movie_id}?api_key={self.api_key}&append_to_response=credits,videos"
            details_response = requests.get(details_url, timeout=10)
            
            if details_response.status_code != 200:
                return {"error": f"TMDB API details request failed: {details_response.status_code}"}
            
            data = details_response.json()
            
            # Extract cast members
            cast = []
            for person in data.get("credits", {}).get("cast", [])[:5]:  # Get top 5 cast members
                cast.append(person.get("name", ""))
            
            # Extract director
            director = ""
            for person in data.get("credits", {}).get("crew", []):
                if person.get("job") == "Director":
                    director = person.get("name", "")
                    break
            
            # Map TMDB response to our format
            movie_info = {
                "title": data.get("title", query),
                "release_date": data.get("release_date", ""),
                "director": director,
                "cast": cast,
                "rating": f"{data.get('vote_average', '')}/10",
                "description": data.get("overview", ""),
                "genre": ", ".join([genre.get("name", "") for genre in data.get("genres", [])]),
                "poster": f"https://image.tmdb.org/t/p/w500{data.get('poster_path', '')}" if data.get("poster_path") else "",
                "backdrop": f"https://image.tmdb.org/t/p/w1280{data.get('backdrop_path', '')}" if data.get("backdrop_path") else "",
                "year": data.get("release_date", "")[:4] if data.get("release_date") else "",
                "runtime": f"{data.get('runtime', '')} min" if data.get("runtime") else "",
                "budget": data.get("budget", ""),
                "revenue": data.get("revenue", "")
            }
            
            # Get trailer if available
            trailers = []
            for video in data.get("videos", {}).get("results", []):
                if video.get("type") == "Trailer" and video.get("site") == "YouTube":
                    trailers.append({
                        "title": video.get("name", ""),
                        "link": f"https://youtube.com/watch?v={video.get('key', '')}",
                        "video_id": video.get("key", "")
                    })
            
            return {
                "raw_results": data,
                "structured_info": movie_info,
                "trailers": trailers
            }
            
        except Exception as e:
            return {"error": f"TMDB search failed: {str(e)}"}
