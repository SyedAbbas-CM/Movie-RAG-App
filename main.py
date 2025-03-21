#!/usr/bin/env python3
"""
Movie Research RAG Agent
A tool for retrieving information about movies and TV shows using LangChain and official APIs.
"""

import sys
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer

# Load environment variables from .env file (if exists)
load_dotenv()

def setup_logging():
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Set up logging with timestamp in filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Use utf-8 encoding for file handler to fix encoding issues
    file_handler = logging.FileHandler(
        f"logs/movie_rag_{timestamp}.log", 
        encoding='utf-8'
    )
    
    # Configure stream handler to use utf-8 encoding for console output
    stream_handler = logging.StreamHandler()
    
    # Configure formatting
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)
    
    # Log system info
    logging.info(f"Python version: {sys.version}")
    logging.info(f"Platform: {sys.platform}")
def check_api_keys():
    """Check if required API keys are set and return status messages."""
    api_keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "OMDB_API_KEY": os.getenv("OMDB_API_KEY"),
        "YOUTUBE_API_KEY": os.getenv("YOUTUBE_API_KEY"),
        "TMDB_API_KEY": os.getenv("TMDB_API_KEY")
    }
    
    messages = []
    for key, value in api_keys.items():
        if value:
            messages.append(f"[OK] {key} is set")
        else:
            if key in ["OPENAI_API_KEY", "OMDB_API_KEY", "YOUTUBE_API_KEY"]:
                messages.append(f"[MISSING] {key} is missing (required)")
            else:
                messages.append(f"[WARNING] {key} is missing (optional)")
    
    return messages

def main():
    """Main entry point for the application."""
    # Set up logging
    setup_logging()
    
    # Start the application
    app = QApplication(sys.argv)
    
    # Create splash screen
    splash_pixmap = QPixmap(400, 300)
    splash_pixmap.fill(Qt.GlobalColor.white)
    splash = QSplashScreen(splash_pixmap)
    
    # Add text to splash screen
    splash.showMessage(
        "Movie Research RAG Agent\nStarting up...", 
        Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom,
        Qt.GlobalColor.black
    )
    splash.show()
    
    # Check API keys
    logging.info("Checking API keys...")
    api_key_messages = check_api_keys()
    for message in api_key_messages:
        logging.info(message)
    
    # Allow splash to show for a moment
    def finish_loading():
        # Import gui module here for slightly faster startup
        from gui import MovieResearchApp
        
        # Get API keys from environment variables
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        omdb_api_key = os.getenv("OMDB_API_KEY", "")
        youtube_api_key = os.getenv("YOUTUBE_API_KEY", "")
        tmdb_api_key = os.getenv("TMDB_API_KEY", "")
        
        # Create and show the main window
        window = MovieResearchApp(openai_api_key, omdb_api_key, youtube_api_key, tmdb_api_key)
        window.show()
        splash.finish(window)
    
    # Use a timer to delay the main window display
    QTimer.singleShot(1500, finish_loading)
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()