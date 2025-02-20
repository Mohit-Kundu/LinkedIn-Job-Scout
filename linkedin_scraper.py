import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, time as dt_time
import pytz
import os
import logging

class LinkedInJobScraper:
    def __init__(self, config_path='config/metadata.json'):
        self.config_path = config_path
        self.config = self.load_config()
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self.timezone = pytz.timezone(self.config.get('time_zone', 'Asia/Kolkata'))

    def load_config(self):
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def update_config(self, key, value):
        self.config[key] = value
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def initialize_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument("--window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        self.driver = webdriver.Chrome(options=options)

    def is_within_time_window(self):
        current_time = datetime.now(self.timezone)
        
        # Parse start and end times
        start_time_str = self.config.get('start_time', '09:00')
        end_time_str = self.config.get('end_time', '18:00')
        
        start_hour, start_minute = map(int, start_time_str.split(':'))
        end_hour, end_minute = map(int, end_time_str.split(':'))
        
        start_time = dt_time(start_hour, start_minute)
        end_time = dt_time(end_hour, end_minute)
        
        current_time_obj = current_time.time()
        
        if start_time <= end_time:
            return start_time <= current_time_obj <= end_time
        else:  # Handle case where end_time is on next day
            return current_time_obj >= start_time or current_time_obj <= end_time

    def get_time_window_for_search(self):
        """Determine the appropriate time window for job search"""
        if not self.config.get("last_scrape_time"):
            # First run - use start_time
            current_date = datetime.now(self.timezone).date()
            start_hour, start_minute = map(int, self.config['start_time'].split(':'))
            start_datetime = datetime.combine(current_date, dt_time(start_hour, start_minute))
            start_datetime = self.timezone.localize(start_datetime)
            
            seconds_since_start = (datetime.now(self.timezone) - start_datetime).total_seconds()
            return max(seconds_since_start, 0)
        else:
            # Subsequent runs - use data_freshness_in_hours
            return int(self.config['data_freshness_in_hours'] * 3600)

    def get_job_listings(self, job_title):
        self.logger.info(f"Starting job search for: {job_title}")
        base_url = "https://www.linkedin.com/jobs/search/"
        
        time_window = self.get_time_window_for_search()
        
        params = {
            "keywords": job_title,
            "location": self.config["location"],
            "f_E": "1",  # Entry level
            "f_TPR": f"r{int(time_window)}"  # Time window in seconds
        }
        
        url = base_url + '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
        self.logger.debug(f"Searching URL: {url}")
        self.driver.get(url)
        
        time.sleep(5)  # Wait for initial load
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait after scroll
        
        jobs = []
        wait = WebDriverWait(self.driver, 20)  # Increased wait time
        
        try:
            selectors = [
                "job-card-container",
                "jobs-search-results__list-item",
                "base-card"
            ]
            
            job_list = None
            for selector in selectors:
                try:
                    job_list = wait.until(EC.presence_of_all_elements_located(
                        (By.CLASS_NAME, selector)))
                    if job_list:
                        break
                except:
                    continue
            
            if not job_list:
                self.logger.error(f"Could not find any job elements for {job_title}")
                return jobs

            self.logger.info(f"Found {len(job_list)} jobs for {job_title}")
            
            for job in job_list:
                try:
                    title = job.find_element(By.CLASS_NAME, "job-card-list__title").text
                    company = job.find_element(By.CLASS_NAME, "job-card-container__company-name").text
                    link = job.find_element(By.CLASS_NAME, "job-card-list__title").get_attribute("href")
                    
                    jobs.append({
                        "title": title,
                        "company": company,
                        "link": link,
                        "experience": "Entry Level"
                    })
                except Exception as e:
                    self.logger.warning(f"Error parsing job card: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error scraping jobs for {job_title}: {str(e)}")
            
        self.logger.info(f"Successfully scraped {len(jobs)} jobs for {job_title}")
        return jobs

    def should_run_scraper(self):
        if self.config["process_busy"]:
            return False
            
        if not self.is_within_time_window():
            self.logger.info("Outside of configured time window, skipping scrape")
            return False
            
        last_scrape = self.config["last_scrape_time"]
        current_time = time.time()
        time_diff = (current_time - last_scrape) / 60  # Convert to minutes
        
        return time_diff >= self.config["auto_scrape_frequency_in_mins"]

    def run(self):
        if not self.should_run_scraper():
            self.logger.info("Skipping scraper run - too soon since last run")
            return None
            
        try:
            self.update_config("process_busy", True)
            self.initialize_driver()
            
            jobs_by_title = {}
            job_titles = [title.strip() for title in self.config["job_titles"].split(",")]
            
            self.logger.info(f"Starting scraping for {len(job_titles)} job titles")
            
            for job_title in job_titles:
                jobs = self.get_job_listings(job_title)
                jobs_by_title[job_title] = jobs
            
            self.update_config("last_scrape_time", time.time())
            self.update_config("process_busy", False)
            
            if self.driver:
                self.driver.quit()
                
            return jobs_by_title
            
        except Exception as e:
            self.logger.error(f"Error in scraper run: {str(e)}")
            self.update_config("process_busy", False)
            if self.driver:
                self.driver.quit()
            raise e 