import os
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.theme import Theme

# Load environment
base_dir = Path(__file__).parent.parent
load_dotenv(base_dir / ".env")

# --- Themes & Logging ---
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green bold",
    "directive": "magenta italic",
})
console = Console(theme=custom_theme)

# --- Config Class ---
class Config:
    def __init__(self):
        self.AGENT_DIR = base_dir
        self.EXECUTION_DIR = base_dir / "execution"
        self.DIRECTIVES_DIR = base_dir / "directives"
        self.TMP_DIR = base_dir / ".tmp"
        self.RESEARCH_DIR = base_dir.parent / "Writing" / "Research"
        
        self.TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        
        # Ensure directories exist
        for d in [self.TMP_DIR, self.RESEARCH_DIR]:
            d.mkdir(parents=True, exist_ok=True)

configs = Config()

# --- Shared Retry logic ---
def retry(max_attempts=3, delay=1):
    def decorator(func):
        import time
        from functools import wraps
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise e
                    console.print(f"[warning]Attempt {attempts} failed: {e}. Retrying...[/]")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator
