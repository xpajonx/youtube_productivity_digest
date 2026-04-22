import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from execution.video_discoverer import VideoDiscoverer
from execution.video_analyzer import VideoAnalyzer
from execution.digest_formatter import DigestFormatter
from execution.digest_mailer import DigestMailer
from execution.config import configs, console

# Load .env explicitly
load_dotenv(configs.AGENT_DIR / ".env")

def load_telos():
    telos = {}
    paths = {
        "mission": configs.AGENT_DIR / "telos" / "MISSION.md",
        "beliefs": configs.AGENT_DIR / "telos" / "BELIEFS.md",
        "goals": configs.AGENT_DIR / "telos" / "GOALS.md"
    }
    for key, path in paths.items():
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                telos[key] = f.read()
        else:
            telos[key] = "Not provided."
    return telos

def run_orchestrator(send_email: bool = True):
    console.print(f"\n[bold magenta]🚀 Weekly Intelligence Digest Orchestrator[/bold magenta]")
    console.print(f"[dim]Initiated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/]\n")
    
    # 1. Discovery
    discoverer = VideoDiscoverer()
    videos = discoverer.discover(days_ago=7)
    
    if not videos:
        console.print("[warning]No trending videos found in the last 7 days. Exiting.[/]")
        return

    # 2. Analysis
    telos_context = load_telos()
    analyzer = VideoAnalyzer()
    results = []
    
    for video in videos:
        console.print(f"\n[info]Processing:[/] [bold]{video['title']}[/]")
        analysis = analyzer.analyze(video, telos_context)
        
        if "error" not in analysis:
            results.append({
                "video": video,
                "analysis": analysis
            })
            console.print(f"[success]Analysis complete for: {video['title']}[/]")
        else:
            console.print(f"[warning]Skipped {video['title']}: {analysis['error']}[/]")

    if not results:
        console.print("[error]No successful analyses. Orchestration aborted.[/]")
        return

    # 3. Formatting
    formatter = DigestFormatter()
    html_report = formatter.format(results)
    
    # Save local copy for reference
    report_path = configs.TMP_DIR / f"digest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_report)
    console.print(f"\n[success]Local report saved to:[/] {report_path}")

    # 4. Delivery
    if send_email:
        mailer = DigestMailer()
        success = mailer.send(html_report)
        
        if success:
            # Update Archive
            archive_path = configs.AGENT_DIR / "memory" / "RESEARCH_ARCHIVE.md"
            with open(archive_path, "a", encoding="utf-8") as f:
                f.write(f"\n## Weekly Digest - {datetime.now().strftime('%Y-%m-%d')}\n")
                for r in results:
                    f.write(f"- **{r['video']['title']}**: {r['analysis']['core_thesis']}\n")
            console.print("[success]Research Archive updated.[/]")
    else:
        console.print("[info]Email delivery skipped (Dry Run).[/]")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-send", action="store_true", help="Skip email delivery")
    args = parser.parse_args()
    
    run_orchestrator(send_email=not args.no_send)
