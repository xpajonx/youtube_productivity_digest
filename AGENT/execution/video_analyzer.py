import subprocess
import os
import json
import requests
import re
from typing import Dict, Optional
from execution.config import configs, console

class VideoAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        # Use provided key or fetch from environment (matching previous Groq setup)
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = "llama-3.3-70b-versatile" # Premium Llama 3 model for analysis

    def _get_transcript(self, video_url: str) -> Optional[str]:
        """Extract transcript using yt-dlp."""
        console.print(f"[info]Extracting transcript for {video_url}...[/]")
        
        # We use yt-dlp to download subtitles/auto-subs without the video
        # -o temp_transcript: output template
        # --skip-download: only subs
        # --write-auto-subs: fallback to auto-generated
        # --extractor-args: use different clients to bypass bot detection
        cmd = [
            "yt-dlp",
            "--write-auto-subs",
            "--skip-download",
            "--sub-format", "vtt/srt",
            "-o", "temp_transcript",
            "--no-warnings",
            "--extractor-args", "youtube:player-client=android,web",
            video_url
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                console.print(f"[warning]yt-dlp failed for {video_url}: {result.stderr.strip()}[/]")
                return None
                
            # Find the generated subtitle file
            # yt-dlp usually appends .en.vtt or similar
            content = None
            for file in os.listdir("."):
                if file.startswith("temp_transcript") and (file.endswith(".vtt") or file.endswith(".srt")):
                    with open(file, "r", encoding="utf-8") as f:
                        raw_content = f.read()
                    os.remove(file)
                    # Clean up VTT/SRT noise (timestamps, tags)
                    content = re.sub(r'<[^>]+>', '', raw_content)
                    content = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}', '', content)
                    content = re.sub(r'\d+\n', '', content) # Remove line numbers
                    content = ' '.join(content.split()) # Normalize whitespace
                    break
            return content
        except Exception as e:
            console.print(f"[error]Failed to extract transcript: {e}[/]")
            return None

    def analyze(self, video_data: Dict, telos_context: Dict) -> Dict:
        """Analyze video using Groq Llama 3 and TELOS context."""
        if not self.api_key:
            return {"error": "GROQ_API_KEY not found in .env."}
            
        transcript = self._get_transcript(video_data['url'])
        if not transcript:
            return {"error": "No transcript available for this video."}
            
        prompt = f"""
Analyze this podcast transcript for a user with the following TELOS (Mission, Beliefs, Goals).
The report must be high-density, authoritative, and follow the "Senior Research Editor" persona.

USER TELOS:
- MISSION: {telos_context['mission']}
- BELIEFS: {telos_context['beliefs']}
- GOALS: {telos_context['goals']}

VIDEO TITLE: {video_data['title']}
UPLOADER: {video_data['uploader']}
URL: {video_data['url']}

TRANSCRIPT SNIPPET (MAX 12000 CHARS):
{transcript[:12000]}

REQUIRED OUTPUT (STRICT JSON ONLY, NO PREAMBLE):
{{
  "core_thesis": "One-sentence executive summary.",
  "key_arguments": ["Point 1", "Point 2", "Point 3"],
  "mental_models": ["Model 1", "Model 2"],
  "actionable_task": "A specific task for the user's Obsidian vault or workflow.",
  "telos_alignment": "How this specific content serves the user's mission or beliefs."
}}
"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a Senior Research Editor. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        try:
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            return json.loads(content)
        except Exception as e:
            console.print(f"[error]Groq analysis failed: {e}[/]")
            return {"error": str(e)}

if __name__ == "__main__":
    pass
