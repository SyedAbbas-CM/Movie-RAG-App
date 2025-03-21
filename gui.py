"""
gui.py
Implements the graphical user interface for the Movie Research Assistant using PyQt6.
"""

import sys
import os
import json
import requests
import traceback
from typing import Dict, List, Any, Optional, Callable
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QLineEdit, QPushButton, QLabel, QScrollArea, QFrame,
    QSplitter, QMessageBox, QFileDialog, QProgressBar, QComboBox,
    QTabWidget, QToolButton, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QUrl, QTimer
from PyQt6.QtGui import QPixmap, QImage, QIcon, QFont, QDesktopServices

# Import the RAG agent
# This import is commented out to allow the file to be viewed independently
# from rag_agent import MovieRAGAgent, SimpleMovieRAGAgent

class ImageLoader(QThread):
    """Thread for loading images from URLs."""
    
    image_loaded = pyqtSignal(QPixmap)
    
    def __init__(self, url: str):
        super().__init__()
        self.url = url
    
    def run(self):
        try:
            response = requests.get(self.url, timeout=10)
            if response.status_code == 200:
                image = QImage()
                image.loadFromData(response.content)
                pixmap = QPixmap.fromImage(image)
                self.image_loaded.emit(pixmap)
        except Exception as e:
            print(f"Error loading image: {e}")


class QueryWorker(QThread):
    """Thread for processing user queries with the RAG agent."""
    
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, agent, query: str):
        super().__init__()
        self.agent = agent
        self.query = query
    
    def run(self):
        try:
            result = self.agent.process_query(self.query)
            self.result_ready.emit(result)
        except Exception as e:
            traceback_text = traceback.format_exc()
            self.error_occurred.emit(f"Error: {str(e)}\n\n{traceback_text}")


class MessageWidget(QFrame):
    """Widget for displaying messages in the conversation."""
    
    link_clicked = pyqtSignal(str)
    
    def __init__(self, message: str, message_type: str = "response", parent=None):
        super().__init__(parent)
        self.message = message
        self.message_type = message_type
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Style the widget based on the message type
        if self.message_type == "user":
            self.setStyleSheet("""
                background-color: #E3F2FD; 
                border-radius: 10px; 
                padding: 10px;
                margin-left: 50px;
            """)
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        elif self.message_type == "tool":
            self.setStyleSheet("""
                background-color: #F5F5F5; 
                border-radius: 5px; 
                padding: 5px; 
                color: #757575; 
                font-style: italic;
                margin-right: 50px;
            """)
        elif self.message_type in ["search-result", "youtube-result"]:
            self.setStyleSheet("""
                background-color: #F5F5F5; 
                border-radius: 5px; 
                padding: 8px; 
                border-left: 4px solid #2196F3; 
                font-family: monospace;
                margin-right: 50px;
            """)
        else:  # response
            self.setStyleSheet("""
                background-color: white; 
                border-radius: 10px; 
                padding: 10px; 
                border: 1px solid #E0E0E0;
                margin-right: 50px;
            """)
        
        # Process message text to find and make URLs clickable
        message = self.message
        url_pattern = r'https?://\S+'
        import re
        
        # Find all URLs in the message
        urls = re.findall(url_pattern, message)
        
        # If no URLs, just add the message as a label
        if not urls:
            message_label = QLabel(message)
            message_label.setWordWrap(True)
            message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            layout.addWidget(message_label)
        else:
            # Split the message by URLs and create labels with clickable links
            parts = re.split(url_pattern, message)
            
            for i, part in enumerate(parts):
                # Add the text part
                if part:
                    text_label = QLabel(part)
                    text_label.setWordWrap(True)
                    text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                    layout.addWidget(text_label)
                
                # Add the URL if there is one
                if i < len(urls):
                    url = urls[i]
                    link_label = QLabel(f'<a href="{url}">{url}</a>')
                    link_label.setOpenExternalLinks(True)
                    link_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
                    layout.addWidget(link_label)


class MovieDetailWidget(QWidget):
    """Widget for displaying detailed movie information with poster."""
    
    def __init__(self, movie_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.movie_info = movie_info
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Set styling for the widget
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f8f8;
                border-radius: 10px;
                padding: 0px;
            }
            QLabel {
                color: #333333;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: bold;
                color: #2196F3;
            }
            QLabel#info {
                font-size: 13px;
                margin-top: 5px;
            }
            QLabel#description {
                font-size: 13px;
                margin-top: 10px;
                color: #555555;
            }
        """)
        
        # Create a horizontal layout for poster and info
        content_layout = QHBoxLayout()
        
        # Poster section
        if self.movie_info.get("poster") and self.movie_info["poster"] != "N/A":
            poster_widget = QLabel()
            poster_widget.setFixedSize(150, 225)
            poster_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            poster_widget.setStyleSheet("background-color: #e0e0e0; border-radius: 5px;")
            poster_widget.setText("Loading poster...")
            
            # Load poster image asynchronously
            self.load_image(self.movie_info["poster"], poster_widget)
            
            content_layout.addWidget(poster_widget)
        
        # Info section
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(8)
        
        # Title
        title_label = QLabel(self.movie_info.get("title", "Unknown Movie"))
        title_label.setObjectName("title")
        info_layout.addWidget(title_label)
        
        # Basic info grid
        info_grid = QVBoxLayout()
        
        # Year, runtime, rating in one row
        basic_info = []
        if self.movie_info.get("year"):
            basic_info.append(f"Year: {self.movie_info['year']}")
        if self.movie_info.get("runtime"):
            basic_info.append(f"Runtime: {self.movie_info['runtime']}")
        if self.movie_info.get("rating"):
            basic_info.append(f"Rating: {self.movie_info['rating']}")
        
        if basic_info:
            basic_info_label = QLabel(" | ".join(basic_info))
            basic_info_label.setObjectName("info")
            info_grid.addWidget(basic_info_label)
        
        # Genre
        if self.movie_info.get("genre"):
            genre_label = QLabel(f"Genre: {self.movie_info['genre']}")
            genre_label.setObjectName("info")
            info_grid.addWidget(genre_label)
        
        # Director
        if self.movie_info.get("director"):
            director_label = QLabel(f"Director: {self.movie_info['director']}")
            director_label.setObjectName("info")
            info_grid.addWidget(director_label)
        
        # Cast
        if self.movie_info.get("cast") and len(self.movie_info["cast"]) > 0:
            cast_text = ", ".join(self.movie_info["cast"])
            cast_label = QLabel(f"Cast: {cast_text}")
            cast_label.setWordWrap(True)
            cast_label.setObjectName("info")
            info_grid.addWidget(cast_label)
        
        # Add info grid to layout
        info_layout.addLayout(info_grid)
        
        # Add a spacer to push content to the top
        info_layout.addStretch(1)
        
        # Add info widget to content layout
        content_layout.addWidget(info_widget, 1)  # 1 is the stretch factor
        
        # Add content layout to main layout
        main_layout.addLayout(content_layout)
        
        # Plot/description
        if self.movie_info.get("description"):
            description_label = QLabel(self.movie_info["description"])
            description_label.setWordWrap(True)
            description_label.setObjectName("description")
            description_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            main_layout.addWidget(description_label)
    
    def load_image(self, url, label):
        """Load an image from URL and set it on the label."""
        self.image_loader = ImageLoader(url)
        self.image_loader.image_loaded.connect(lambda pixmap: label.setPixmap(
            pixmap.scaled(label.width(), label.height(), Qt.AspectRatioMode.KeepAspectRatio)
        ))
        self.image_loader.start()


class TrailerWidget(QWidget):
    """Widget for displaying movie trailer information."""
    
    def __init__(self, trailer_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.trailer_info = trailer_info
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        # Set styling
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border-radius: 8px;
                padding: 8px;
            }
            QLabel#title {
                font-weight: bold;
            }
            QPushButton {
                background-color: #FF0000;
                color: white;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #CC0000;
            }
        """)
        
        # Thumbnail if available
        if self.trailer_info.get("thumbnail"):
            thumbnail_label = QLabel()
            thumbnail_label.setFixedSize(120, 68)  # 16:9 ratio
            thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumbnail_label.setStyleSheet("background-color: #e0e0e0;")
            
            # Load thumbnail
            self.load_image(self.trailer_info["thumbnail"], thumbnail_label)
            
            layout.addWidget(thumbnail_label)
        
        # Info section
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        
        # Title
        title_label = QLabel(self.trailer_info.get("title", "Trailer"))
        title_label.setObjectName("title")
        title_label.setWordWrap(True)
        info_layout.addWidget(title_label)
        
        # Channel if available
        if self.trailer_info.get("channel"):
            channel_label = QLabel(f"Channel: {self.trailer_info['channel']}")
            info_layout.addWidget(channel_label)
        
        # Add spacer
        info_layout.addStretch(1)
        
        # Watch button
        if self.trailer_info.get("link"):
            button_layout = QHBoxLayout()
            watch_button = QPushButton("Watch Trailer")
            watch_button.setFixedWidth(120)
            watch_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.trailer_info["link"])))
            button_layout.addWidget(watch_button)
            button_layout.addStretch(1)
            info_layout.addLayout(button_layout)
        
        layout.addWidget(info_widget, 1)  # 1 is the stretch factor
    
    def load_image(self, url, label):
        """Load an image from URL and set it on the label."""
        self.image_loader = ImageLoader(url)
        self.image_loader.image_loaded.connect(lambda pixmap: label.setPixmap(
            pixmap.scaled(label.width(), label.height(), Qt.AspectRatioMode.KeepAspectRatio)
        ))
        self.image_loader.start()


class MovieResultsWidget(QWidget):
    """Widget for displaying multiple movie search results."""
    
    def __init__(self, movies: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.movies = movies
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Set styling for the widget
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f8f8;
                border-radius: 10px;
                padding: 10px;
            }
            QLabel.title {
                font-size: 16px;
                font-weight: bold;
                color: #2196F3;
            }
            QLabel.relevance {
                color: #4CAF50;
                font-weight: bold;
            }
        """)
        
        # Add header
        header = QLabel(f"Found {len(self.movies)} movies:")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(header)
        
        # Add scroll area for results
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Add each movie result
        for movie in self.movies:
            movie_widget = QWidget()
            movie_layout = QHBoxLayout(movie_widget)
            
            # Add poster if available
            if movie.get("poster") and movie["poster"] != "N/A":
                poster_label = QLabel()
                poster_label.setFixedSize(80, 120)
                poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                poster_label.setStyleSheet("background-color: #e0e0e0; border-radius: 5px;")
                
                # Load poster image asynchronously
                self.load_image(movie["poster"], poster_label)
                
                movie_layout.addWidget(poster_label)
            
            # Info section
            info_widget = QWidget()
            info_layout = QVBoxLayout(info_widget)
            
            # Title with relevance score
            title_layout = QHBoxLayout()
            title = QLabel(movie.get("title", "Unknown Movie"))
            title.setProperty("class", "title")
            title_layout.addWidget(title)
            
            if movie.get("relevance_score"):
                relevance = QLabel(f"Relevance: {movie['relevance_score']}%")
                relevance.setProperty("class", "relevance")
                title_layout.addWidget(relevance)
                title_layout.addStretch(1)
            
            info_layout.addLayout(title_layout)
            
            # Basic info
            if movie.get("year") or movie.get("genre") or movie.get("rating"):
                details = []
                if movie.get("year"):
                    details.append(f"Year: {movie['year']}")
                if movie.get("genre"):
                    details.append(f"Genre: {movie['genre']}")
                if movie.get("rating"):
                    details.append(f"Rating: {movie['rating']}")
                
                info_label = QLabel(" | ".join(details))
                info_layout.addWidget(info_label)
            
            # Brief description (truncated)
            if movie.get("description"):
                desc = movie["description"]
                if len(desc) > 150:
                    desc = desc[:147] + "..."
                desc_label = QLabel(desc)
                desc_label.setWordWrap(True)
                info_layout.addWidget(desc_label)
            
            movie_layout.addWidget(info_widget, 1)
            
            # Add separator line
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            
            scroll_layout.addWidget(movie_widget)
            scroll_layout.addWidget(separator)
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
    
    def load_image(self, url, label):
        """Load an image from URL and set it on the label."""
        image_loader = ImageLoader(url)
        image_loader.image_loaded.connect(lambda pixmap: label.setPixmap(
            pixmap.scaled(label.width(), label.height(), Qt.AspectRatioMode.KeepAspectRatio)
        ))
        image_loader.start()


class MovieResearchApp(QMainWindow):
    """Main application window."""
    
    def __init__(self, openai_api_key, omdb_api_key, youtube_api_key, tmdb_api_key=None):
        super().__init__()
        
        # Initialize the RAG agent
        from rag_agent import MovieRAGAgent, SimpleMovieRAGAgent
        
        # Choose agent type based on availability of API keys
        if all([openai_api_key, omdb_api_key, youtube_api_key]):
            self.agent = MovieRAGAgent(openai_api_key, omdb_api_key, youtube_api_key, tmdb_api_key)
            self.agent_type = "LangChain Agent"
        elif all([omdb_api_key, youtube_api_key]):
            # Use SimpleMovieRAGAgent as fallback if no OpenAI API key
            self.agent = SimpleMovieRAGAgent("", omdb_api_key, youtube_api_key)
            self.agent_type = "Simple RAG"
        else:
            self.agent = None
            self.agent_type = "None"
        
        self.init_ui()
    
    def init_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Movie Research Assistant")
        self.setGeometry(100, 100, 900, 700)
        
        # Main widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Create a toolbar/header
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # App title
        title_label = QLabel("Movie Research Assistant")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3;")
        toolbar_layout.addWidget(title_label)
        
        # Add spacer to push buttons to the right
        toolbar_layout.addStretch(1)
        
        # Add tools/options
        agent_type_label = QLabel(f"Agent: {self.agent_type}")
        agent_type_label.setStyleSheet("color: #555;")
        toolbar_layout.addWidget(agent_type_label)
        
        # Clear chat button
        clear_button = QToolButton()
        clear_button.setText("Clear")
        clear_button.setToolTip("Clear conversation")
        clear_button.clicked.connect(self.clear_conversation)
        toolbar_layout.addWidget(clear_button)
        
        # Save/load buttons
        save_button = QToolButton()
        save_button.setText("Save")
        save_button.setToolTip("Save conversation")
        save_button.clicked.connect(self.save_conversation)
        toolbar_layout.addWidget(save_button)
        
        load_button = QToolButton()
        load_button.setText("Load")
        load_button.setToolTip("Load conversation")
        load_button.clicked.connect(self.load_conversation)
        toolbar_layout.addWidget(load_button)
        
        # Add toolbar to main layout
        main_layout.addWidget(toolbar)
        
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)
        
        # Create a splitter for adjustable panels
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter, 1)  # 1 is the stretch factor
        
        # Conversation area (scrollable)
        conversation_container = QWidget()
        conversation_layout = QVBoxLayout(conversation_container)
        conversation_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.conversation_widget = QWidget()
        self.conversation_layout = QVBoxLayout(self.conversation_widget)
        self.conversation_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.conversation_layout.setSpacing(10)
        self.conversation_layout.setContentsMargins(10, 10, 10, 10)
        
        self.scroll_area.setWidget(self.conversation_widget)
        conversation_layout.addWidget(self.scroll_area)
        
        # Debug/details area with tabs
        details_container = QWidget()
        details_layout = QVBoxLayout(details_container)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Tool calls tab
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setStyleSheet("font-family: monospace; font-size: 12px;")
        tabs.addTab(self.details_text, "Tool Calls")
        
        # Raw data tab
        self.raw_data_text = QTextEdit()
        self.raw_data_text.setReadOnly(True)
        self.raw_data_text.setStyleSheet("font-family: monospace; font-size: 12px;")
        tabs.addTab(self.raw_data_text, "Raw Data")
        
        details_layout.addWidget(tabs)
        
        # Add both containers to the splitter
        splitter.addWidget(conversation_container)
        splitter.addWidget(details_container)
        
        # Set initial sizes (70% conversation, 30% details)
        splitter.setSizes([500, 200])
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask something about a movie or TV show...")
        self.input_field.returnPressed.connect(self.send_message)
        
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        input_layout.addWidget(self.input_field, 1)  # 1 is the stretch factor
        input_layout.addWidget(send_button)
        
        # Add input area to main layout
        main_layout.addLayout(input_layout)
        
        self.setCentralWidget(central_widget)
        
        # Add progress bar for loading indication
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(5)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)
        
        # Add welcome message
        self.add_message("Welcome to the Movie Research Assistant! Ask me about any movie or TV show.", "response")
    
    def send_message(self):
        """Process user input and get response from the agent."""
        user_input = self.input_field.text().strip()
        if not user_input:
            return
        
        # Check if agent is initialized
        if self.agent is None:
            QMessageBox.warning(
                self, 
                "Agent Not Initialized", 
                "API keys are missing. This is a demo mode only.\n\nPlease set OPENAI_API_KEY, OMDB_API_KEY, and YOUTUBE_API_KEY environment variables to use the full functionality."
            )
            return
        
        # Add user message to conversation
        self.add_message(user_input, "user")
        self.input_field.clear()
        
        # Show loading indicator
        self.progress_bar.show()
        self.add_message("Searching for information...", "tool")
        
        # Process the query with the agent in a separate thread
        self.worker = QueryWorker(self.agent, user_input)
        self.worker.result_ready.connect(self.handle_result)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()
    
    def handle_result(self, result):
        """Handle the result from the RAG agent."""
        # Hide progress bar
        self.progress_bar.hide()
        
        # Display tool call results in the details panel
        details_text = ""
        for tool_call in result.get("tool_calls", []):
            tool_name = tool_call.get("tool", "Unknown Tool")
            tool_input = tool_call.get("input", "")
            
            # Simplify output for display
            if "output" in tool_call:
                if isinstance(tool_call["output"], dict) and "raw_results" in tool_call["output"]:
                    # Don't show raw results in the UI
                    output_copy = tool_call["output"].copy()
                    if "raw_results" in output_copy:
                        output_copy["raw_results"] = "... (omitted for brevity)"
                    tool_output = output_copy
                else:
                    tool_output = tool_call["output"]
            else:
                tool_output = {}
            
            details_text += f"Tool: {tool_name}\n"
            details_text += f"Input: {tool_input}\n"
            details_text += f"Output: {json.dumps(tool_output, indent=2)}\n\n"
        
        self.details_text.setText(details_text)
        
        # Display raw data in the raw data tab
        self.raw_data_text.setText(json.dumps(result, indent=2))
        
        # Remove the typing indicator
        self.remove_typing_indicator()
        
        # Check for semantic search results
        semantic_results = None
        for tool_call in result.get("tool_calls", []):
            if tool_call.get("tool") == "SemanticMovieSearch" and "output" in tool_call:
                if "results" in tool_call["output"] and tool_call["output"]["results"]:
                    semantic_results = tool_call["output"]["results"]
            elif tool_call.get("tool") == "MovieRecommendations" and "output" in tool_call:
                if "recommendations" in tool_call["output"] and tool_call["output"]["recommendations"]:
                    semantic_results = tool_call["output"]["recommendations"]
        
        # Display semantic search results if available
        if semantic_results and len(semantic_results) > 0:
            results_widget = MovieResultsWidget(semantic_results)
            self.conversation_layout.addWidget(results_widget)
        
        # Display movie information with poster if available
        movie_info = result.get("movie_info", {})
        if movie_info and movie_info.get("title"):
            movie_widget = MovieDetailWidget(movie_info)
            self.conversation_layout.addWidget(movie_widget)
        
        # Display YouTube trailer information
        trailer_info = result.get("trailer_info", [])
        if trailer_info and len(trailer_info) > 0:
            # Use the first trailer
            trailer_widget = TrailerWidget(trailer_info[0])
            self.conversation_layout.addWidget(trailer_widget)
        
        # Show final response
        self.add_message(result.get("response", "No response generated."), "response")
    
    def handle_error(self, error_message):
        """Handle errors from the RAG agent."""
        # Hide progress bar
        self.progress_bar.hide()
        
        # Remove the typing indicator
        self.remove_typing_indicator()
        
        # Show error message
        self.add_message(f"Error: {error_message}", "response")
        
        # Debug output
        self.details_text.setText(error_message)
    
    def add_message(self, message, message_type="response"):
        """Add a message to the conversation area."""
        message_widget = MessageWidget(message, message_type)
        self.conversation_layout.addWidget(message_widget)
        
        # Scroll to the bottom
        QApplication.processEvents()
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def remove_typing_indicator(self):
        """Remove the last message if it's a typing indicator."""
        items_count = self.conversation_layout.count()
        if items_count > 0:
            last_item = self.conversation_layout.itemAt(items_count - 1)
            if last_item and isinstance(last_item.widget(), MessageWidget):
                widget = last_item.widget()
                if widget.message_type == "tool" and "Searching" in widget.message:
                    self.conversation_layout.removeWidget(widget)
                    widget.deleteLater()
    
    def clear_conversation(self):
        """Clear the conversation history."""
        # Ask for confirmation
        reply = QMessageBox.question(
            self, 
            "Clear Conversation", 
            "Are you sure you want to clear the conversation history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear the conversation layout
            while self.conversation_layout.count():
                item = self.conversation_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            
            # Clear agent conversation history
            if self.agent:
                self.agent.clear_conversation()
            
            # Add welcome message
            self.add_message("Conversation cleared. Ask me about any movie or TV show!", "response")
    
    def save_conversation(self):
        """Save the conversation history to a file."""
        if not self.agent:
            QMessageBox.warning(self, "Save Error", "No agent initialized. Cannot save conversation.")
            return
        
        # Open file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Conversation",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            if self.agent.save_conversation(file_path):
                QMessageBox.information(self, "Save Successful", f"Conversation saved to {file_path}")
            else:
                QMessageBox.warning(self, "Save Error", "Failed to save conversation")
    
    def load_conversation(self):
        """Load conversation history from a file."""
        if not self.agent:
            QMessageBox.warning(self, "Load Error", "No agent initialized. Cannot load conversation.")
            return
        
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Conversation",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            if self.agent.load_conversation(file_path):
                # Clear current conversation display
                while self.conversation_layout.count():
                    item = self.conversation_layout.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
                
                # Display loaded conversation
                history = self.agent.get_conversation_history()
                for msg in history:
                    self.add_message(msg["content"], msg["role"])
                
                QMessageBox.information(self, "Load Successful", f"Conversation loaded from {file_path}")
            else:
                QMessageBox.warning(self, "Load Error", "Failed to load conversation")


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for consistent appearance
    
    # Get API keys from environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    omdb_api_key = os.getenv("OMDB_API_KEY", "")
    youtube_api_key = os.getenv("YOUTUBE_API_KEY", "")
    tmdb_api_key = os.getenv("TMDB_API_KEY", "")
    
    # Create and show the main window
    window = MovieResearchApp(openai_api_key, omdb_api_key, youtube_api_key, tmdb_api_key)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
