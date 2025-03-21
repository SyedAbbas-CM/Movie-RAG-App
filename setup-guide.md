# Movie RAG Agent: Setup Guide

This guide walks you through the complete setup process for the Movie Research RAG Agent, from obtaining API keys to running the application.

## 1. Getting the Required API Keys

Before running the application, you'll need to obtain the necessary API keys. Here's how to get each one:

### 1.1 OpenAI API Key

This key is used for the language model that powers the RAG agent.

1. Go to [OpenAI's website](https://platform.openai.com/signup) and create an account if you don't have one
2. Once logged in, navigate to the [API keys page](https://platform.openai.com/account/api-keys)
3. Click "Create new secret key" and give it a name (e.g., "Movie RAG Agent")
4. Copy the key (it will only be shown once)

### 1.2 OMDb API Key

This key is used to retrieve movie information.

1. Visit [OMDb API Key page](http://www.omdbapi.com/apikey.aspx)
2. Select the FREE tier (1,000 daily requests)
3. Fill out the form with your email address
4. Check your email and click the verification link
5. Your API key will be provided after verification

### 1.3 YouTube Data API Key

This key is used to search for movie trailers.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. In the sidebar, go to "APIs & Services" > "Library"
4. Search for "YouTube Data API v3" and click on it
5. Click "Enable" to activate the API for your project
6. Go to "APIs & Services" > "Credentials"
7. Click "Create Credentials" > "API key"
8. Copy your new API key

### 1.4 TMDB API Key (Optional)

This key provides additional movie details and better posters.

1. Create an account on [The Movie Database](https://www.themoviedb.org/signup)
2. Go to your account settings by clicking on your profile icon
3. Select the "API" section from the left sidebar
4. Click "Create" under "Request an API Key"
5. Select "Developer" option
6. Fill out the form with your details
7. Once approved, you'll receive your API key

## 2. Installation

### 2.1 Clone the Repository

First, clone the repository to your local machine:

```bash
git clone https://github.com/yourusername/movie-rag-agent.git
cd movie-rag-agent
```

If you downloaded the code as a ZIP file, extract it and navigate to the folder in your terminal.

### 2.2 Set Up a Virtual Environment

It's recommended to use a virtual environment to avoid package conflicts:

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 2.3 Install Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

This will install:
- LangChain and related packages
- PyQt6 for the user interface
- Chroma DB and Sentence Transformers for vector database
- Google API client for YouTube
- Other utility packages

### 2.4 Configure API Keys

Create a file named `.env` in the project root directory and add your API keys:

```
OPENAI_API_KEY=your_openai_key_here
OMDB_API_KEY=your_omdb_key_here
YOUTUBE_API_KEY=your_youtube_key_here
TMDB_API_KEY=your_tmdb_key_here  # Optional
```

Replace the placeholder text with your actual API keys.

## 3. Running the Application

With everything set up, you can now run the application:

```bash
python main.py
```

The application will:
1. Check for your API keys
2. Show a splash screen while loading
3. Initialize the vector database
4. Display the main user interface

## 4. Troubleshooting

### 4.1 Missing API Keys

If you see warnings about missing API keys, check that:
- Your `.env` file is in the correct location (project root directory)
- The API key variable names match exactly (OPENAI_API_KEY, etc.)
- There are no spaces around the equals sign
- You've activated your virtual environment

### 4.2 Import Errors

If you see import errors for packages like `langchain` or `PyQt6`, ensure you've:
- Installed all dependencies with `pip install -r requirements.txt`
- Activated your virtual environment

### 4.3 API Rate Limits

If you encounter errors about API rate limits:
- OMDb has a limit of 1,000 requests per day on the free tier
- YouTube Data API has a quota of 10,000 units per day
- OpenAI has rate limits based on your account tier

### 4.4 Vector Database Errors

If you see errors related to the vector database:
- Ensure the `db` directory has proper write permissions
- Try deleting the `db` directory and let the application recreate it

## 5. Using the Application

### 5.1 Basic Usage

1. Type your query in the input field at the bottom
2. Press Enter or click "Send"
3. View the results in the conversation area

### 5.2 Example Queries

Try these example queries to see what the system can do:

- "Tell me about Inception"
- "Who directed The Shawshank Redemption?"
- "Show me the trailer for Avengers: Endgame"
- "Find sci-fi movies about time travel"
- "What are some movies similar to The Matrix?"
- "What are the best comedies from the 90s?"

### 5.3 Saving Conversations

You can save your conversation history:
1. Click the "Save" button in the top bar
2. Choose a location to save the JSON file
3. To load a saved conversation, click "Load" and select the file

## 6. Technical Support

If you encounter issues not covered in this guide:
1. Check the log files in the `logs` directory for error messages
2. Ensure all your API keys are valid and have the necessary permissions
3. Verify you're using Python 3.8 or higher
4. Make sure all dependencies are correctly installed

## 7. Conclusion

You've now set up the Movie Research RAG Agent and are ready to use it for finding movie information, watching trailers, and discovering new films through semantic search. Enjoy exploring!

If you make improvements to the code, consider contributing back to the project by submitting a pull request.
