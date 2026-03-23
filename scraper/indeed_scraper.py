import json
import time
from datetime import datetime
from typing import List, Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from utils.helpers import human_delay, save_json


def setup_indeed_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


class IndeedScraper:
    BASE_URL = "https://in.indeed.com/jobs"
    
    def __init__(self):
        self.driver = setup_indeed_driver()
        self.jobs_data: List[Dict] = []
    
    def build_url(self, search_term: str, location: str, page: int = 0) -> str:
        from urllib.parse import quote
        q = quote(search_term)
        l = quote(location)
        return f"{self.BASE_URL}?q={q}&l={l}&start={page * 10}"
    
    def extract_job_data(self, card) -> Dict:
        try:
            title = card.find_element(By.CSS_SELECTOR, 'h2.jobTitle a, h2.jobTitle span').text.strip()
        except NoSuchElementException:
            title = ""
        
        try:
            company = card.find_element(By.CSS_SELECTOR, '[data-testid="company-name"], .companyName').text.strip()
        except NoSuchElementException:
            company = ""
        
        try:
            location = card.find_element(By.CSS_SELECTOR, '[data-testid="text-location"], .companyLocation').text.strip()
        except NoSuchElementException:
            location = ""
        
        try:
            salary = card.find_element(By.CSS_SELECTOR, '.salary-snippet').text.strip()
        except NoSuchElementException:
            salary = ""
        
        try:
            posted = card.find_element(By.CSS_SELECTOR, '.date, [class*="date"], [class*="age"]').text.strip()
        except NoSuchElementException:
            posted = ""
        
        try:
            description = card.find_element(By.CSS_SELECTOR, '.job-snippet').text.strip()
        except NoSuchElementException:
            description = ""
        
        return {
            "title": title,
            "company": company,
            "location": location,
            "salary": salary,
            "posted_date": posted,
            "description": description or title,
        }
    
    def scrape_jobs(
        self,
        search_term: str,
        location: str = "India",
        max_jobs: int = 50,
        pages: int = 5
    ) -> List[Dict]:
        jobs = []
        
        for page in range(pages):
            if len(jobs) >= max_jobs:
                break
            
            url = self.build_url(search_term, location, page)
            print(f"  Page {page + 1}")
            
            self.driver.get(url)
            human_delay(3, 5)
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".job_seen_beacon"))
                )
            except TimeoutException:
                print("    No jobs found")
                break
            
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job_seen_beacon")
            
            if not job_cards:
                break
            
            for card in job_cards:
                if len(jobs) >= max_jobs:
                    break
                
                job = self.extract_job_data(card)
                
                if job.get("title"):
                    job["search_term"] = search_term
                    job["search_location"] = location
                    job["scraped_at"] = datetime.now().isoformat()
                    jobs.append(job)
                    self.jobs_data.append(job)
                
                human_delay(0.5, 1.0)
            
            print(f"    Found {len(jobs)} jobs total")
            human_delay(1, 2)
            
            print(f"    Found {len(jobs)} jobs total")
            human_delay(1, 2)
        
        return jobs
    
    def save_raw_data(self, filepath: str = "data/raw_jobs.json"):
        save_json(self.jobs_data, filepath)
        return filepath
    
    def close(self):
        self.driver.quit()


def run_indeed_scraper(
    search_terms: List[str] = None,
    locations: List[str] = None,
    max_jobs_per_search: int = 30
):
    if search_terms is None:
        search_terms = [
            "Data Analyst",
            "Data Scientist", 
            "Data Engineer",
            "Business Analyst",
            "Machine Learning Engineer"
        ]
    
    if locations is None:
        locations = [
            "India",
            "Bangalore",
            "Mumbai",
            "Delhi",
            "Hyderabad",
            "Chennai",
            "Pune"
        ]
    
    all_jobs = []
    scraper = IndeedScraper()
    
    try:
        for term in search_terms:
            for loc in locations:
                print(f"\n>>> {term} in {loc}")
                jobs = scraper.scrape_jobs(term, loc, max_jobs=max_jobs_per_search)
                all_jobs.extend(jobs)
                human_delay(3, 5)
    finally:
        scraper.close()
    
    if all_jobs:
        save_json(all_jobs, "data/raw_jobs.json")
    
    print(f"\n=== Total: {len(all_jobs)} jobs ===")
    return all_jobs


if __name__ == "__main__":
    run_indeed_scraper(
        search_terms=["Data Analyst", "Data Scientist"],
        locations=["India", "Bangalore"],
        max_jobs_per_search=20
    )
