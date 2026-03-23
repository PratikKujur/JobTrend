import json
import time
import random
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from utils.helpers import setup_driver, human_delay, save_json


class LinkedInScraper:
    def __init__(self, headless: bool = True):
        self.driver = setup_driver(headless=headless)
        self.jobs_data: List[Dict] = []

    def scroll_to_load(self, iterations: int = 3):
        for _ in range(iterations):
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            human_delay(1.5, 2.5)

    def extract_job_card(self, card) -> Optional[Dict]:
        try:
            title_elem = card.find_element(
                By.CSS_SELECTOR, "h3.job-card-container__title"
            )
            company_elem = card.find_element(
                By.CSS_SELECTOR, "h4.job-card-container__subtitle"
            )
            location_elem = card.find_element(
                By.CSS_SELECTOR, "span.job-card-container__metadata-item"
            )
            
            return {
                "title": title_elem.text.strip(),
                "company": company_elem.text.strip(),
                "location": location_elem.text.strip(),
            }
        except Exception:
            return None

    def extract_job_details(self) -> Dict:
        details = {"description": "", "posted_date": "", "experience": ""}
        
        try:
            desc_elem = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.show-more-less-html__markup")
                )
            )
            details["description"] = desc_elem.text.strip()
        except Exception:
            pass

        try:
            date_elem = self.driver.find_element(
                By.CSS_SELECTOR, "spanposted-time-ago__text"
            )
            details["posted_date"] = date_elem.text.strip()
        except Exception:
            pass

        return details

    def scrape_jobs(
        self,
        search_term: str,
        location: str = "India",
        max_jobs: int = 50,
        pages: int = 5
    ) -> List[Dict]:
        query = search_term.replace(" ", "%20")
        location_query = location.replace(" ", "%20")
        url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={location_query}"
        
        self.driver.get(url)
        human_delay(3, 5)
        
        job_cards = []
        for page in range(pages):
            self.scroll_to_load(2)
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "li.jobs-search-results__list-item")
                )
            )
            
            cards = self.driver.find_elements(
                By.CSS_SELECTOR, "li.jobs-search-results__list-item"
            )
            
            for card in cards:
                if len(job_cards) >= max_jobs:
                    break
                    
                job_info = self.extract_job_card(card)
                if job_info:
                    try:
                        card.click()
                        human_delay(1, 2)
                        
                        job_details = self.extract_job_details()
                        job_info.update(job_details)
                        job_info["scraped_at"] = datetime.now().isoformat()
                        job_info["search_term"] = search_term
                        job_info["search_location"] = location
                        
                        job_cards.append(job_info)
                        self.jobs_data.append(job_info)
                        
                        if len(job_cards) >= max_jobs:
                            break
                    except Exception:
                        continue
            
            if len(job_cards) >= max_jobs:
                break
                
            try:
                next_btn = self.driver.find_element(
                    By.CSS_SELECTOR, "button[aria-label='Page next']"
                )
                if "disabled" in next_btn.get_attribute("class"):
                    break
                next_btn.click()
                human_delay(2, 3)
            except Exception:
                break

        return job_cards

    def save_raw_data(self, filepath: str = "data/raw_jobs.json"):
        save_json(self.jobs_data, filepath)
        return filepath

    def close(self):
        self.driver.quit()


def run_scraper(search_term: str = "Data Analyst", location: str = "India", max_jobs: int = 50):
    scraper = LinkedInScraper(headless=True)
    try:
        print(f"Scraping {max_jobs} jobs for '{search_term}' in {location}...")
        jobs = scraper.scrape_jobs(search_term, location, max_jobs)
        filepath = scraper.save_raw_data()
        print(f"Scraped {len(jobs)} jobs. Saved to {filepath}")
        return jobs
    finally:
        scraper.close()


if __name__ == "__main__":
    jobs = run_scraper("Data Analyst", "India", 30)
