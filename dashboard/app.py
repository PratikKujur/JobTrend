import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict


API_BASE = "https://jobtrend.onrender.com"


@st.cache_data(ttl=300)
def fetch_data(endpoint: str) -> Dict:
    try:
        response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return {}


@st.cache_data(ttl=300)
def fetch_jobs(location: str = None, experience: str = None) -> List[Dict]:
    params = []
    if location:
        params.append(f"location={location}")
    if experience:
        params.append(f"experience={experience}")
    query = "&".join(params) if params else ""
    endpoint = f"/jobs?{query}" if query else "/jobs"
    data = fetch_data(endpoint)
    return data.get("jobs", [])


def main():
    st.set_page_config(
        page_title="Job Market Intelligence",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Job Market Intelligence Dashboard")
    st.markdown("Real-time job market analytics powered by scraped LinkedIn data")
    
    with st.spinner("Loading data..."):
        stats = fetch_data("/stats")
        top_skills = fetch_data("/skills/top?limit=15")
        locations = fetch_data("/locations")
        experience_dist = fetch_data("/experience")
    
    if not stats:
        st.error("⚠️ Could not connect to API. Make sure the FastAPI server is running.")
        st.code("uvicorn api.main:app --reload")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Jobs", stats.get("total_jobs", 0))
    with col2:
        st.metric("Companies", stats.get("total_companies", 0))
    with col3:
        st.metric("Skills Tracked", stats.get("total_skills", 0))
    with col4:
        st.metric("Remote Jobs", stats.get("remote_jobs", 0), 
                  delta=f"{stats.get('remote_percentage', 0)}%")
    
    st.divider()
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("🔥 Top In-Demand Skills")
        if top_skills:
            skills_df = pd.DataFrame(top_skills)
            fig = px.bar(
                skills_df.head(15),
                x="job_count",
                y="name",
                orientation="h",
                color="job_count",
                color_continuous_scale="Blues",
                title="Most Requested Skills"
            )
            fig.update_layout(
                yaxis=dict(autorange="reversed"),
                showlegend=False,
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No skill data available")
    
    with col_right:
        st.subheader("📍 Jobs by Location")
        if locations:
            loc_df = pd.DataFrame(locations)
            fig = px.pie(
                loc_df.head(10),
                values="job_count",
                names="location",
                hole=0.4,
                title="Job Distribution"
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No location data available")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("📈 Experience Level Distribution")
        if experience_dist:
            exp_df = pd.DataFrame(experience_dist)
            fig = px.pie(
                exp_df,
                values="count",
                names="experience_level",
                hole=0.4,
                color="experience_level",
                color_discrete_map={
                    "Entry": "#2ecc71",
                    "Mid": "#3498db",
                    "Senior": "#9b59b6",
                    "Not Specified": "#95a5a6"
                }
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        st.subheader("🏢 Top Hiring Companies")
        jobs = fetch_jobs()
        if jobs:
            company_counts = pd.Series([j.get("company") for j in jobs]).value_counts().head(10)
            fig = px.bar(
                x=company_counts.index,
                y=company_counts.values,
                color=company_counts.values,
                color_continuous_scale="Viridis",
                title="Top Companies by Job Count"
            )
            fig.update_layout(
                xaxis_title="Company",
                yaxis_title="Number of Jobs",
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.subheader("🔍 Job Listings")
    
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        location_filter = st.text_input("Filter by Location", "")
    with col_filter2:
        experience_filter = st.selectbox(
            "Experience Level",
            ["All", "Entry", "Mid", "Senior", "Not Specified"]
        )
    
    filtered_jobs = fetch_jobs(
        location=location_filter if location_filter else None,
        experience=experience_filter if experience_filter != "All" else None
    )
    
    if filtered_jobs:
        df = pd.DataFrame(filtered_jobs)
        df_display = df[["title", "company", "location", "experience_level", "is_remote"]].copy()
        df_display.columns = ["Title", "Company", "Location", "Experience", "Remote"]
        df_display["Remote"] = df_display["Remote"].map({True: "✓", False: "✗"})
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True
        )
        
        st.caption(f"Showing {len(df_display)} jobs")
    else:
        st.info("No jobs found matching your criteria")


if __name__ == "__main__":
    main()
