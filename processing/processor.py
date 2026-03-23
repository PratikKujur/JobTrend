import json
from pathlib import Path
from datetime import datetime

import pandas as pd
from dateutil import parser as date_parser


SKILLS_LIST = [
    "Python", "SQL", "Java", "JavaScript", "TypeScript", "R", "Scala", "Go", "Rust",
    "Excel", "Power BI", "Tableau", "Looker", "Qlik",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
    "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "Keras",
    "Spark", "Hadoop", "Kafka", "Airflow", "dbt",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
    "Git", "Jenkins", "CI/CD", "Agile", "Scrum",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "Statistics", "A/B Testing", "ETL", "Data Warehousing",
    "Salesforce", "SAP", "Oracle", "Snowflake", "Databricks",
    "Data Analysis", "Data Analytics", "Analytics", "Reporting",
    "Business Intelligence", "BI", "DAX", "ETL", "SSIS", "SSRS",
    "Unix", "Linux", "Shell", "Bash",
    "S3", "EC2", "Lambda", "BigQuery",
    "C++", "C#", ".NET", "Ruby",
    "Vue", "React", "Angular", "Node",
    "Mongo", "DynamoDB", "Cassandra",
    "Jira", "Confluence", "GitHub", "GitLab",
]


def load_raw_data(filepath: str = "data/raw_jobs.json") -> pd.DataFrame:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    return df


def clean_text(text: str) -> str:
    if pd.isna(text):
        return ""
    text = str(text).strip()
    text = " ".join(text.split())
    return text


def extract_skills(description: str, title: str = "") -> list:
    import re
    text = f"{description} {title}".lower()
    if not text.strip():
        return []
    found_skills = []
    for skill in SKILLS_LIST:
        skill_lower = skill.lower()
        pattern = r'\b' + re.escape(skill_lower) + r'\b'
        if re.search(pattern, text):
            found_skills.append(skill)
    return found_skills


def infer_skills_from_title(title: str) -> list:
    title_lower = title.lower()
    skills = []
    skill_patterns = {
        "Power BI": ["power bi", "powerbi"],
        "Business Intelligence": ["business intelligence", "bi developer", "bi analyst"],
        "Data Science": ["data scientist", "data science"],
        "Machine Learning": ["machine learning", "ml engineer", "ml scientist"],
        "Data Engineering": ["data engineer", "de "],
        "SQL": ["sql", "mysql", "postgresql", "plsql"],
        "Python": ["python"],
        "R": ["r programming", "rstudio"],
        "Excel": ["excel"],
        "Tableau": ["tableau"],
        "AWS": ["aws"],
        "Azure": ["azure"],
        "ETL": ["etl"],
        "Reporting": ["reporting", "reports"],
        "Analytics": ["analytics", "analyst"],
        "Statistics": ["statistics", "statistical"],
        "Scala": ["scala"],
        "Spark": ["spark"],
        "Hadoop": ["hadoop"],
        "Kafka": ["kafka"],
    }
    for skill, patterns in skill_patterns.items():
        for pattern in patterns:
            if pattern in title_lower:
                skills.append(skill)
                break
    return list(set(skills))


def extract_experience(description: str) -> dict:
    import re
    exp_info = {"min_years": None, "max_years": None, "raw": None}
    
    patterns = [
        r"(\d+)\+?\s*years?\s+(?:of\s+)?experience",
        r"(\d+)\s*-\s*(\d+)\s+years?\s+(?:of\s+)?experience",
        r"minimum\s+(\d+)\s+years?",
        r"at\s+least\s+(\d+)\s+years?",
        r"(\d+)\+\s+years?",
    ]
    
    combined = " ".join(patterns)
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            exp_info["raw"] = match.group(0)
            if len(match.groups()) == 2:
                exp_info["min_years"] = int(match.group(1))
                exp_info["max_years"] = int(match.group(2))
            else:
                exp_info["min_years"] = int(match.group(1))
            break
    
    return exp_info


def determine_experience_level(min_years: int) -> str:
    if min_years is None:
        return "Not Specified"
    elif min_years <= 2:
        return "Entry"
    elif min_years <= 5:
        return "Mid"
    else:
        return "Senior"


def is_remote(location: str, title: str) -> bool:
    text = f"{location} {title}".lower()
    remote_indicators = ["remote", "work from home", "wfh", "anywhere"]
    return any(ind in text for ind in remote_indicators)


def parse_posted_date(posted_str: str) -> str:
    if not posted_str:
        return datetime.now().date().isoformat()
    try:
        posted_lower = posted_str.lower()
        if "hour" in posted_lower:
            return datetime.now().date().isoformat()
        elif "day" in posted_lower:
            import re
            match = re.search(r"(\d+)", posted_str)
            if match:
                days = int(match.group(1))
                return (datetime.now() - pd.Timedelta(days=days)).date().isoformat()
        return datetime.now().date().isoformat()
    except Exception:
        return datetime.now().date().isoformat()


def process_jobs(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["title", "company", "location"])
    
    df["title"] = df["title"].apply(clean_text)
    df["company"] = df["company"].apply(clean_text)
    df["location"] = df["location"].apply(clean_text)
    df["description"] = df["description"].apply(clean_text)
    
    df["skills"] = df.apply(
        lambda row: list(set(
            extract_skills(row.get("description", ""), row.get("title", "")) +
            infer_skills_from_title(row.get("title", ""))
        )), axis=1
    )
    df["skills_count"] = df["skills"].apply(len)
    
    experience_data = df["description"].apply(extract_experience)
    df["min_experience"] = experience_data.apply(lambda x: x["min_years"])
    df["max_experience"] = experience_data.apply(lambda x: x["max_years"])
    df["experience_raw"] = experience_data.apply(lambda x: x["raw"])
    
    df["experience_level"] = df["min_experience"].apply(determine_experience_level)
    df["is_remote"] = df.apply(
        lambda row: is_remote(row["location"], row["title"]), axis=1
    )
    
    df["posted_date"] = df["posted_date"].apply(parse_posted_date)
    
    return df


def save_clean_data(df: pd.DataFrame, filepath: str = "data/clean_jobs.csv"):
    df.to_csv(filepath, index=False, encoding="utf-8")
    return filepath


def get_skill_stats(df: pd.DataFrame) -> pd.DataFrame:
    all_skills = []
    for skills in df["skills"]:
        all_skills.extend(skills)
    
    skill_counts = pd.Series(all_skills).value_counts().reset_index()
    skill_counts.columns = ["skill", "count"]
    return skill_counts


def run_processor(raw_path: str = "data/raw_jobs.json", clean_path: str = "data/clean_jobs.csv"):
    print("Loading raw data...")
    df = load_raw_data(raw_path)
    print(f"Loaded {len(df)} jobs")
    
    print("Processing jobs...")
    df = process_jobs(df)
    
    print("Saving clean data...")
    save_clean_data(df, clean_path)
    print(f"Saved {len(df)} clean jobs to {clean_path}")
    
    skill_stats = get_skill_stats(df)
    print("\nTop 10 Skills:")
    print(skill_stats.head(10).to_string(index=False))
    
    return df


if __name__ == "__main__":
    run_processor()
