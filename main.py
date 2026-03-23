import subprocess
import sys
from pathlib import Path

from processing.processor import run_processor
from database.models import run_db_pipeline


def run_pipeline():
    print("=" * 50)
    print("Job Market Intelligence Pipeline")
    print("=" * 50)
    
    print("\n[1/2] Processing raw data...")
    try:
        df = run_processor(
            raw_path="data/raw_jobs.json",
            clean_path="data/clean_jobs.csv"
        )
        print(f"Processed {len(df)} jobs successfully")
    except FileNotFoundError:
        print("No raw data found. Run scraper first or add data/raw_jobs.json")
        return
    
    print("\n[2/2] Loading to database...")
    try:
        stats = run_db_pipeline(clean_csv="data/clean_jobs.csv")
        print(f"Database ready: {stats['total_jobs']} jobs, {stats['total_skills']} skills")
    except Exception as e:
        print(f"Database error: {e}")
    
    print("\n" + "=" * 50)
    print("Pipeline complete!")
    print("=" * 50)
    print("\nTo start the API server:")
    print("  uvicorn api.main:app --reload")
    print("\nTo start the dashboard:")
    print("  streamlit run dashboard/app.py")


def run_scraper_demo():
    print("Scraper requires LinkedIn credentials and browser automation.")
    print("This is a demo mode using sample data.")
    print("\nTo run the full scraper:")
    print("  python scraper/linkedin_scraper.py")


def start_api():
    subprocess.run([sys.executable, "-m", "uvicorn", "api.main:app", "--reload"])


def start_dashboard():
    subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard/app.py"])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "scrape":
            run_scraper_demo()
        elif cmd == "process":
            run_processor()
        elif cmd == "db":
            run_db_pipeline()
        elif cmd == "pipeline":
            run_pipeline()
        elif cmd == "api":
            start_api()
        elif cmd == "dashboard":
            start_dashboard()
        else:
            print("Commands: scrape, process, db, pipeline, api, dashboard")
    else:
        run_pipeline()
