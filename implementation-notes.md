# Implementation Notes: Movie RAG Agent

This document details my implementation journey, challenges faced, and key design decisions for the Movie Research RAG Agent project.

## Introduction

As a beginner to Retrieval Augmented Generation (RAG) systems, I wanted to build a practical application that would help me understand the core concepts while creating something useful. I chose to focus on movie information since it's a domain with:

1. Readily available APIs for data retrieval
2. Rich visual elements for an engaging UI
3. Natural language query potential
4. A good fit for semantic search capabilities

## Development Approach

I used an iterative development approach, starting with the core functionality and gradually adding features:

1. **Phase 1:** Basic movie information retrieval with OMDb API
2. **Phase 2:** Added YouTube trailer search capability
3. **Phase 3:** Implemented vector database for semantic search
4. **Phase 4:** Enhanced the UI with posters and trailer views
5. **Phase 5:** Added LangChain integration for improved query handling

## Key Design Decisions

### 1. Modular Architecture

I structured the application with clear separation of concerns:

- **rag_agent.py**: Central coordinator that doesn't know API implementation details
- **search_tools.py**: API integration isolated from agent logic
- **vector_store.py**: Vector database operations independent of agent
- **gui.py**: UI that's decoupled from backend logic

This made it easier to:
- Replace components (e.g., switching from OMDb to another movie database)
- Test individual components in isolation
- Add new features without breaking existing functionality

### 2. LangChain Agent Framework

I chose LangChain's agent framework for several reasons:

- Built-in tool-calling capabilities
- Conversation memory handling
- Structured response formatting
- OpenAI Functions integration

The agent pattern was perfect for this application as it allows the LLM to decide which tools to use based on the user's query.

### 3. Local Vector Database

For semantic search and recommendations, I used Chroma DB with a local persistence layer:

- Stores embeddings on disk for persistence between sessions
- Uses Sentence Transformers for embedding generation
- Provides fast similarity search capabilities
- Doesn't require cloud services or complex setup

### 4. PyQt for UI

I selected PyQt6 for the user interface because:

- Rich widget library
- Cross-platform compatibility
- Support for asynchronous operations
- Ability to display images and create custom widgets

## Technical Challenges and Solutions

### Challenge 1: API Integration Complexity

**Problem:** Each API (OMDb, YouTube, TMDB) has different authentication methods, request formats, and response structures.

**Solution:** I created adapter classes for each API that:
- Handle authentication specifics
- Format requests properly
- Transform responses into a standardized format
- Manage error handling

Example from `search_tools.py`:
```python
def search(self, query: str) -> Dict[str, Any]:
    try:
        # API-specific request code...
        
        # Transform response to standard format
        movie_info = {
            "title": data.get("Title", query),
            "release_date": data.get("Released", ""),
            "director": data.get("Director", ""),
            # More fields...
        }
        
        return {
            "raw_results": data,
            "structured_info": movie_info
        }
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}
```

### Challenge 2: Vector Embeddings for Movies

**Problem:** Creating effective embeddings for movies requires combining multiple attributes (title, plot, genre, etc.) in a meaningful way.

**Solution:** I constructed a comprehensive text representation for each movie:

```python
# Create searchable text from movie info
search_text = f"{movie_info.get('title', '')} ({movie_info.get('year', '')}). "
search_text += f"Directed by {movie_info.get('director', '')}. "
search_text += f"Starring {', '.join(movie_info.get('cast', [])[:3])}. "
search_text += f"Genre: {movie_info.get('genre', '')}. "
search_text += movie_info.get('description', '')
```

This approach ensures that searches consider multiple aspects of the movie, not just the title or description.

### Challenge 3: Asynchronous UI Updates

**Problem:** API calls and vector database operations could freeze the UI.

**Solution:** I implemented a threaded approach using QThread:

```python
class QueryWorker(QThread):
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def run(self):
        try:
            result = self.agent.process_query(self.query)
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))
```

This keeps the UI responsive while processing queries and loading images.

### Challenge 4: LangChain Integration

**Problem:** Setting up LangChain's agent framework with the right tools and prompt templates.

**Solution:** I used the OpenAI Functions agent with a carefully designed system prompt:

```python
system_prompt = """You are a helpful movie research assistant. 
Your goal is to help the user find information about movies and TV shows.
You have access to several tools to help you with this task:

1. OMDbMovieSearch: Use this to search for general information about movies
2. YouTubeSearch: Use this to find trailer videos for movies
3. TMDBMovieSearch: Use this to find detailed information about movies
4. SemanticMovieSearch: Use this for natural language searches
5. MovieRecommendations: Use this to find similar movies

For each user query, determine what kind of information they need:
- If they ask about a specific movie, use OMDbMovieSearch
- If they want to see a trailer, use YouTubeSearch
...
"""
```

And I used LangChain's new LCEL (LangChain Expression Language) for cleaner code:

```python
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
```

## Lessons Learned

1. **Start Simple**: Beginning with basic API calls before adding vector search was the right approach. It allowed me to test core functionality early.

2. **API Reliability**: External APIs can have rate limits and occasional downtime. Adding error handling early saved me trouble later.

3. **Data Standardization**: Creating a consistent data format across different sources made the agent logic much simpler.

4. **UI Responsiveness**: Keeping the UI responsive during long-running operations is critical for user experience.

5. **Vector Quality Matters**: The quality of vector embeddings significantly impacts semantic search results. Spending time to create good text representations was worth the effort.

## Next Steps

If I were to continue developing this project, I would focus on:

1. **User Profiles**: Adding user accounts to remember preferences and viewing history
2. **Content-Based Filtering**: Implementing more sophisticated recommendation algorithms
3. **Local Caching**: Reducing API calls by caching commonly requested movies
4. **Voice Interface**: Adding speech recognition and synthesis for a hands-free experience
5. **More Data Sources**: Integrating additional sources like Rotten Tomatoes, IMDb ratings, and streaming availability

## Conclusion

Building this RAG system taught me a lot about combining language models with structured data retrieval. The key insight was that RAG isn't just about improving accuracy through retrieval - it's about creating a system that can reliably bring together different types of information to provide a comprehensive, contextual response to user queries.
