# YouTube Intelligence Digest

Automated system for discovering trending YouTube videos in specific niches (Writing, Productivity, AI Agents), analyzing them using Groq (Llama 3), and sending a formatted HTML digest via email.

## Features
- **Discovery**: Uses `yt-dlp` to find high-engagement videos from the last 7 days.
- **Analysis**: Extracts transcripts and uses LLM (Groq Llama 3) to analyze alignment with user's TELOS (Mission, Beliefs, Goals).
- **Delivery**: Sends a rich HTML report via Gmail.
- **Archive**: Automatically updates a local research archive with findings.

## Project Structure
- `AGENT/execution/`: Core logic and scripts.
- `AGENT/telos/`: User's mission, beliefs, and goals for LLM context.
- `AGENT/memory/`: Persistent storage for digest archives.
- `.github/workflows/`: GitHub Actions for weekly automated runs.

## Setup
1.  **Clone the repository**.
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Environment Variables**: Create a `.env` file in the root (or `AGENT/`) with:
    - `GROQ_API_KEY`
    - `GMAIL_USER`
    - `GMAIL_APP_PASSWORD`
    - `REPORT_RECIPIENT_EMAIL`
4.  **Local Run**:
    ```bash
    set PYTHONPATH=AGENT
    python AGENT/execution/weekly_digest_orchestrator.py
    ```
    Use `--no-send` for dry runs.

## Automation
The system is configured to run every Sunday at 09:00 UTC via GitHub Actions.
Make sure to add the required secrets to your GitHub repository settings.
