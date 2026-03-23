from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import (
    get_all_jobs,
    get_top_skills,
    get_jobs_by_skill,
    get_location_stats,
    get_experience_distribution,
    get_summary_stats,
    init_db,
)


app = FastAPI(
    title="Job Market Intelligence API",
    description="API for job market data analysis",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str]
    experience_level: Optional[str]
    is_remote: bool
    posted_date: Optional[str]


class SkillResponse(BaseModel):
    name: str
    job_count: int


class LocationStats(BaseModel):
    location: str
    job_count: int


class ExperienceDist(BaseModel):
    experience_level: str
    count: int


class SummaryStats(BaseModel):
    total_jobs: int
    total_companies: int
    total_skills: int
    remote_jobs: int
    remote_percentage: float


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def root():
    return {"message": "Job Market Intelligence API", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/jobs", response_model=JobListResponse)
def list_jobs(
    location: Optional[str] = Query(None, description="Filter by location"),
    experience: Optional[str] = Query(None, description="Filter by experience level"),
    limit: int = Query(100, ge=1, le=500)
):
    jobs = get_all_jobs(location=location, experience_level=experience, limit=limit)
    return JobListResponse(
        jobs=[
            JobResponse(
                id=j["id"],
                title=j["title"],
                company=j["company"],
                location=j.get("location"),
                experience_level=j.get("experience_level"),
                is_remote=bool(j.get("is_remote", 0)),
                posted_date=j.get("posted_date")
            )
            for j in jobs
        ],
        total=len(jobs)
    )


@app.get("/jobs/{job_id}")
def get_job(job_id: int):
    jobs = get_all_jobs(limit=1000)
    for job in jobs:
        if job["id"] == job_id:
            return job
    raise HTTPException(status_code=404, detail="Job not found")


@app.get("/skills/top", response_model=List[SkillResponse])
def top_skills(limit: int = Query(20, ge=1, le=100)):
    skills = get_top_skills(limit=limit)
    return [SkillResponse(name=s["name"], job_count=s["job_count"]) for s in skills]


@app.get("/skills/{skill_name}/jobs")
def jobs_with_skill(
    skill_name: str,
    limit: int = Query(50, ge=1, le=200)
):
    jobs = get_jobs_by_skill(skill_name, limit=limit)
    return {"skill": skill_name, "jobs": jobs, "total": len(jobs)}


@app.get("/locations", response_model=List[LocationStats])
def locations():
    stats = get_location_stats()
    return [LocationStats(location=s["location"], job_count=s["job_count"]) for s in stats]


@app.get("/experience", response_model=List[ExperienceDist])
def experience_dist():
    dist = get_experience_distribution()
    return [ExperienceDist(experience_level=d["experience_level"], count=d["count"]) for d in dist]


@app.get("/stats", response_model=SummaryStats)
def stats():
    return get_summary_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
