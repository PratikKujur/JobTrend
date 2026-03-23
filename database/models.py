import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
import json

import pandas as pd


DB_PATH = "data/jobs.db"


def init_db(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            description TEXT,
            min_experience INTEGER,
            max_experience INTEGER,
            experience_level TEXT,
            is_remote INTEGER DEFAULT 0,
            posted_date TEXT,
            search_term TEXT,
            scraped_at TEXT,
            UNIQUE(title, company, location)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_skills (
            job_id INTEGER,
            skill_id INTEGER,
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            FOREIGN KEY (skill_id) REFERENCES skills(id),
            PRIMARY KEY (job_id, skill_id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_experience ON jobs(experience_level)
    """)
    
    conn.commit()
    return conn


def load_jobs_to_db(df: pd.DataFrame, db_path: str = DB_PATH):
    conn = init_db(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM job_skills")
    cursor.execute("DELETE FROM skills")
    cursor.execute("DELETE FROM jobs")
    conn.commit()
    
    skill_name_to_id = {}
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT OR IGNORE INTO jobs 
            (title, company, location, description, min_experience, max_experience,
             experience_level, is_remote, posted_date, search_term, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["title"], row["company"], row["location"],
            row.get("description", ""),
            int(row["min_experience"]) if pd.notna(row.get("min_experience")) else None,
            int(row["max_experience"]) if pd.notna(row.get("max_experience")) else None,
            row.get("experience_level", "Not Specified"),
            1 if row.get("is_remote", False) else 0,
            row.get("posted_date"),
            row.get("search_term"),
            row.get("scraped_at")
        ))
        
        job_id = cursor.lastrowid
        if job_id == 0:
            cursor.execute(
                "SELECT id FROM jobs WHERE title=? AND company=? AND location=?",
                (row["title"], row["company"], row["location"])
            )
            result = cursor.fetchone()
            if result:
                job_id = result[0]
        
        skills = row.get("skills", [])
        if isinstance(skills, str):
            try:
                import ast
                skills = ast.literal_eval(skills)
            except Exception:
                skills = []
        
        for skill in skills:
            if skill not in skill_name_to_id:
                cursor.execute("INSERT OR IGNORE INTO skills (name) VALUES (?)", (skill,))
                cursor.execute("SELECT id FROM skills WHERE name=?", (skill,))
                skill_id = cursor.fetchone()[0]
                skill_name_to_id[skill] = skill_id
            else:
                skill_id = skill_name_to_id[skill]
            
            cursor.execute(
                "INSERT OR IGNORE INTO job_skills (job_id, skill_id) VALUES (?, ?)",
                (job_id, skill_id)
            )
    
    conn.commit()
    return conn


def get_all_jobs(
    location: Optional[str] = None,
    experience_level: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []
    
    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if experience_level:
        query += " AND experience_level = ?"
        params.append(experience_level)
    
    query += f" LIMIT {limit}"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df.to_dict("records")


def get_top_skills(limit: int = 20) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT s.name, COUNT(js.skill_id) as job_count
        FROM skills s
        JOIN job_skills js ON s.id = js.skill_id
        GROUP BY s.id
        ORDER BY job_count DESC
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(limit,))
    conn.close()
    return df.to_dict("records")


def get_jobs_by_skill(skill_name: str, limit: int = 50) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT j.* FROM jobs j
        JOIN job_skills js ON j.id = js.job_id
        JOIN skills s ON js.skill_id = s.id
        WHERE s.name = ?
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(skill_name, limit))
    conn.close()
    return df.to_dict("records")


def get_location_stats() -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT location, COUNT(*) as job_count
        FROM jobs
        GROUP BY location
        ORDER BY job_count DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict("records")


def get_experience_distribution() -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT experience_level, COUNT(*) as count
        FROM jobs
        GROUP BY experience_level
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict("records")


def get_summary_stats() -> Dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT company) FROM jobs")
    total_companies = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT skill_id) FROM job_skills")
    total_skills = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE is_remote = 1")
    remote_jobs = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_jobs": total_jobs,
        "total_companies": total_companies,
        "total_skills": total_skills,
        "remote_jobs": remote_jobs,
        "remote_percentage": round(remote_jobs / total_jobs * 100, 1) if total_jobs > 0 else 0
    }


def run_db_pipeline(clean_csv: str = "data/clean_jobs.csv"):
    print("Loading clean data to database...")
    df = pd.read_csv(clean_csv)
    
    if "skills" in df.columns:
        import ast
        df["skills"] = df["skills"].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) else x
        )
    
    load_jobs_to_db(df)
    
    stats = get_summary_stats()
    print(f"Database loaded: {stats['total_jobs']} jobs, {stats['total_skills']} skills")
    
    return stats


if __name__ == "__main__":
    run_db_pipeline()
