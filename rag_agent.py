"""
rag_agent.py
Implements a RAG agent using LangChain for movie information retrieval.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import os
import json

# LangChain imports
from langchain.agents import AgentExecutor, Tool
from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# Import our search tools
from search_tools import OMDbMovieSearchTool, YouTubeSearchTool, TMDBMovieSearchTool
from vector_store import MovieVectorStore

@dataclass
class Message:
    """Represents a message in the conversation history."""
    content: str
    role: str  # 'user', 'assistant', 'tool'
    tool_calls: List[Dict[str, Any]] = None
    tool_results: List[Dict[str, Any]] = None


class MovieRAGAgent:
    """RAG agent for movie information retrieval using LangChain."""
    
    def __init__(self, openai_api_key: str, omdb_api_key: str, youtube_api_key: str, tmdb_api_key: Optional[str] = None):
        """
        Initialize the RAG agent with API keys.
        
        Parameters:
        - openai_api_key (str): OpenAI API key for LangChain
        - omdb_api_key (str): OMDb API key
        - youtube_api_key (str): YouTube Data API key
        - tmdb_api_key (str, optional): TMDB API key
        """
        # Initialize conversation memory
        self.conversation_history = []
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize vector store
        self.vector_store = MovieVectorStore()
        
        # Initialize search tools
        self.omdb_tool = OMDbMovieSearchTool(omdb_api_key)
        self.youtube_tool = YouTubeSearchTool(youtube_api_key)
        self.tmdb_tool = TMDBMovieSearchTool(tmdb_api_key) if tmdb_api_key else None
        
        # Initialize the language model
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            temperature=0.7,
            model_name="gpt-3.5-turbo"
        )
        
        # Define tools for the agent
        tools = [
            Tool(
                name="OMDbMovieSearch",
                func=self.omdb_tool.search,
                description="Search for movie information using the OMDb API. Use this tool when you need to find information about a specific movie such as its director, cast, rating, or plot."
            ),
            Tool(
                name="YouTubeSearch",
                func=self.youtube_tool.search,
                description="Search for movie trailers on YouTube. Use this tool when you need to find a trailer for a specific movie."
            ),
            Tool(
                name="SemanticMovieSearch",
                func=self.semantic_search,
                description="Search for movies using natural language descriptions. Use this when the user asks for movies that match certain themes, topics, or are similar to other movies."
            ),
            Tool(
                name="MovieRecommendations",
                func=self.get_recommendations,
                description="Get movie recommendations similar to a specific movie. Use this when the user asks for movies similar to a particular title."
            )
        ]
        
        # Add TMDB tool if available
        if self.tmdb_tool:
            tools.append(
                Tool(
                    name="TMDBMovieSearch",
                    func=self.tmdb_tool.search,
                    description="Search for movie information using The Movie Database (TMDB) API. This provides more detailed information and is especially good for recent movies."
                )
            )
        
        # Create a system prompt for the agent
        system_prompt = """You are a helpful movie research assistant. 
Your goal is to help the user find information about movies and TV shows.
You have access to several tools to help you with this task:

1. OMDbMovieSearch: Use this to search for general information about movies
2. YouTubeSearch: Use this to find trailer videos for movies
3. TMDBMovieSearch: Use this to find detailed information about movies, especially recent ones
4. SemanticMovieSearch: Use this for natural language searches when the user wants to find movies matching themes, genres, etc.
5. MovieRecommendations: Use this to find similar movies when the user asks for recommendations

For each user query, determine what kind of information they need:
- If they ask about a specific movie, use OMDbMovieSearch or TMDBMovieSearch
- If they want to see a trailer, use YouTubeSearch
- If they ask for movies matching certain criteria or descriptions, use SemanticMovieSearch
- If they want recommendations similar to a movie they like, use MovieRecommendations

Be conversational and helpful. If you're not sure what movie the user is referring to, ask for clarification.
"""
        
        # Create a prompt template for the agent
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create the agent
        from langchain.agents.format_scratchpad import format_to_openai_functions
        from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
        from langchain_core.messages import FunctionMessage

        # Define the LangChain agent
        agent = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: x["chat_history"],
                "agent_scratchpad": lambda x: format_to_openai_functions(x["intermediate_steps"])
            }
            | prompt
            | self.llm.bind_functions(tools)
            | OpenAIFunctionsAgentOutputParser()
        )
        
        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            memory=self.memory,
            return_intermediate_steps=True
        )
    
    def update_vector_store(self, movie_info: Dict[str, Any]) -> str:
        """
        Add movie information to the vector store.
        
        Parameters:
        - movie_info (dict): Movie information to add
        
        Returns:
        - str: ID of the added movie
        """
        return self.vector_store.add_movie(movie_info)
    
    def semantic_search(self, query: str) -> Dict[str, Any]:
        """
        Search for movies using semantic search.
        
        Parameters:
        - query (str): Natural language query
        
        Returns:
        - dict: Search results
        """
        results = self.vector_store.search_movies(query)
        
        return {
            "query": query,
            "results": results,
            "result_count": len(results)
        }
    
    def get_recommendations(self, movie_title: str) -> Dict[str, Any]:
        """
        Get movie recommendations similar to a specified movie.
        
        Parameters:
        - movie_title (str): Title of the movie to get recommendations for
        
        Returns:
        - dict: Recommendation results
        """
        recommendations = self.vector_store.get_recommendations(movie_title)
        
        return {
            "movie": movie_title,
            "recommendations": recommendations,
            "result_count": len(recommendations)
        }
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a user query to retrieve movie information.
        
        Parameters:
        - user_query (str): The user's query about a movie
        
        Returns:
        - dict: Response data including the generated response, tool calls, and movie info
        """
        # Add user message to history
        self.conversation_history.append(Message(content=user_query, role="user"))
        
        # Call the LangChain agent
        result = self.agent_executor.invoke({"input": user_query})
        
        # Extract tool calls and results
        tool_calls = []
        movie_info = {}
        trailer_info = []
        
        for step in result.get("intermediate_steps", []):
            action, observation = step
            
            tool_call = {
                "tool": action.tool,
                "input": action.tool_input,
                "output": observation
            }
            tool_calls.append(tool_call)
            
            # Extract movie and trailer info
            if action.tool == "OMDbMovieSearch" or action.tool == "TMDBMovieSearch":
                if isinstance(observation, dict) and "structured_info" in observation:
                    movie_info = observation.get("structured_info", {})
                    # Add to vector store
                    if movie_info and movie_info.get("title"):
                        self.update_vector_store(movie_info)
                    # If using TMDB, also get built-in trailers
                    if "trailers" in observation and observation["trailers"]:
                        trailer_info = observation["trailers"]
            
            if action.tool == "YouTubeSearch" and not trailer_info:
                if isinstance(observation, list) and len(observation) > 0:
                    trailer_info = observation
        
        # Add assistant message to history
        self.conversation_history.append(
            Message(
                content=result["output"],
                role="assistant",
                tool_calls=tool_calls,
                tool_results={
                    "movie_info": movie_info,
                    "trailer_info": trailer_info
                }
            )
        )
        
        return {
            "response": result["output"],
            "tool_calls": tool_calls,
            "movie_info": movie_info,
            "trailer_info": trailer_info,
            "conversation_history": self.get_conversation_history()
        }
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Return the conversation history in a simplified format.
        
        Returns:
        - list: Conversation history with messages and tool calls
        """
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "tool_calls": msg.tool_calls if hasattr(msg, "tool_calls") and msg.tool_calls else None
            }
            for msg in self.conversation_history
        ]
    
    def clear_conversation(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
        self.memory.clear()
    
    def save_conversation(self, filepath: str) -> bool:
        """
        Save the conversation history to a file.
        
        Parameters:
        - filepath (str): Path to save the conversation history
        
        Returns:
        - bool: True if successful, False otherwise
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.get_conversation_history(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False
    
    def load_conversation(self, filepath: str) -> bool:
        """
        Load conversation history from a file.