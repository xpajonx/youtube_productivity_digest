import subprocess
import json
from datetime import datetime, timedelta
from typing import List, Dict
from execution.config import configs, console

class VideoDiscoverer:
    def __init__(self):
        # Broad niche targets for discovery
        self.niches = ["writing podcast", "productivity podcast", "AI Agent podcast"]

    def discover(self, days_ago: int = 7) -> List[Dict]:
        all_videos = []
        # Calculate date threshold for yt-dlp (format YYYYMMDD)
        threshold_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y%m%d")
        
        for niche in self.niches:
            console.print(f"[info]Searching for: {niche}[/]")
            # yt-dlp search command: 
            # - ytsearch5: Limit to 5 results per niche
            # - --dateafter: Limit to recent videos
            # - --dump-json: Rich metadata for popularity/engagement
            # - --flat-playlist: Fast discovery (doesn't fetch individual video full metadata)
            cmd = [
                "yt-dlp",
                f"ytsearch5:{niche}",
                "--dateafter", threshold_date,
                "--dump-json",
                "--flat-playlist",
                "--quiet"
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                for line in result.stdout.splitlines():
                    if line.strip():
                        video_data = json.loads(line)
                        all_videos.append({
                            "id": video_data.get("id"),
                            "title": video_data.get("title"),
                            "url": f"https://www.youtube.com/watch?v={video_data.get('id')}",
                            "niche": niche,
                            "view_count": video_data.get("view_count", 0),
                            "uploader": video_data.get("uploader"),
                            "upload_date": video_data.get("upload_date")
                        })
            except Exception as e:
                console.print(f"[error]Error searching {niche}: {e}[/]")
        
        # Deduplicate and sort by view count (if available)
        unique_videos = {v['id']: v for v in all_videos}.values()
        sorted_videos = sorted(unique_videos, key=lambda x: x.get('view_count', 0), reverse=True)
        
        # We return top 5 across all niches
        return sorted_videos[:5]

if __name__ == "__main__":
    discoverer = VideoDiscoverer()
    videos = discoverer.discover()
    console.print(f"\n[success]Discovered {len(videos)} Trending Videos:[/]")
    for i, v in enumerate(videos, 1):
        console.print(f"{i}. [bold]{v['title']}[/] ({v['uploader']}) - {v['url']}")
