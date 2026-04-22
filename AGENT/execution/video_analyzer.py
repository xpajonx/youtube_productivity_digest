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
        """Extract transcript using yt-dlp with multi-client fallback."""
        import time
        import random
        
        console.print(f"[info]Extracting transcript for {video_url}...[/]")
        
        # Try multiple client profiles to bypass bot detection
        # Android and iOS are often less restricted than Web
        client_profiles = [
            "android,web",
            "ios",
            "mweb,web"
        ]
        
        for i, profile in enumerate(client_profiles):
            if i > 0:
                wait_time = random.uniform(2, 5)
                console.print(f"[info]Retrying with profile: {profile} (waiting {wait_time:.1f}s)...[/]")
                time.sleep(wait_time)

            cmd = [
                "yt-dlp",
                "--write-auto-subs",
                "--skip-download",
                "--sub-format", "vtt/srt",
                "-o", "temp_transcript",
                "--no-warnings",
                "--extractor-args", f"youtube:player-client={profile}",
                video_url
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    continue # Try next profile
                    
                # Find the generated subtitle file
                content = None
                for file in os.listdir("."):
                    if file.startswith("temp_transcript") and (file.endswith(".vtt") or file.endswith(".srt")):
                        with open(file, "r", encoding="utf-8") as f:
                            raw_content = f.read()
                        os.remove(file)
                        # Clean up VTT/SRT noise
                        content = re.sub(r'<[^>]+>', '', raw_content)
                        content = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}', '', content)
                        content = re.sub(r'\d+\n', '', content)
                        content = ' '.join(content.split())
                        break
                
                if content:
                    return content
                    
            except Exception as e:
                console.print(f"[warning]Attempt with {profile} failed: {e}[/]")
                
        console.print(f"[error]All extraction profiles failed for {video_url}. This video may be blocked or require cookies.[/]")
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
