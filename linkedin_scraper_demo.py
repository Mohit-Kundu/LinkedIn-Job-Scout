import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import logging

class LinkedInJobScraperDemo:
    def __init__(self):
        self.driver = None
        self.logger = logging.getLogger(__name__)
        
        # Demo configuration
        self.job_titles = ["Software Engineer", "Data Scientist"]
        self.location = "United States"
        self.experience_level = "Entry level"
        self.time_window = 30  # minutes
        
    def initialize_driver(self):
        """Initialize Chrome driver with basic settings"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        self.driver = webdriver.Chrome(options=options)
        
    def construct_linkedin_url(self, job_title):
        """Construct LinkedIn search URL with parameters"""
        base_url = "https://www.linkedin.com/jobs/search/?"
        params = {
            "keywords": job_title,
            "location": self.location,
            "f_TPR": f"r{self.time_window}",  # Time: Past 30 minutes
            "f_E": "1",  # Experience level: Entry level
            "position": "1",
            "pageNum": "0"
        }
        return base_url + "&".join(f"{k}={v}" for k, v in params.items())
    
    def extract_job_details(self, job_card):
        """Extract relevant details from a job card"""
        try:
            title = job_card.find_element(By.CSS_SELECTOR, "h3.base-search-card__title").text.strip()
            company = job_card.find_element(By.CSS_SELECTOR, "h4.base-search-card__subtitle").text.strip()
            link = job_card.find_element(By.CSS_SELECTOR, "a.base-card__full-link").get_attribute('href')
            
            return {
                'title': title,
                'company': company,
                'experience': self.experience_level,
                'link': link,
                'scrape_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            self.logger.error(f"Error extracting job details: {str(e)}")
            return None

    def scrape_jobs(self, job_title):
        """Scrape jobs for a specific title"""
        jobs = []
        url = self.construct_linkedin_url(job_title)
        
        try:
            self.driver.get(url)
            time.sleep(3)  # Allow page to load
            
            # Wait for job cards to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.base-card"))
            )
            
            # Get all job cards
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.base-card")
            
            for card in job_cards[:10]:  # Limit to first 10 jobs for demo
                job_details = self.extract_job_details(card)
                if job_details:
                    jobs.append(job_details)
                    
        except Exception as e:
            self.logger.error(f"Error scraping jobs for {job_title}: {str(e)}")
            
        return jobs

    def run(self):
        """Main method to run the scraper"""
        try:
            self.initialize_driver()
            all_jobs = {}
            
            for job_title in self.job_titles:
                self.logger.info(f"Scraping jobs for: {job_title}")
                jobs = self.scrape_jobs(job_title)
                all_jobs[job_title] = jobs
                self.logger.info(f"Found {len(jobs)} jobs for {job_title}")
                
            return all_jobs
            
        except Exception as e:
            self.logger.error(f"Error in scraper run: {str(e)}")
            return None
            
        finally:
            if self.driver:
                self.driver.quit()

def main():
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run the demo scraper
    scraper = LinkedInJobScraperDemo()
    jobs = scraper.run()
    
    # Print results
    if jobs:
        for title, job_list in jobs.items():
            print(f"\nJobs found for {title}:")
            for job in job_list:
                print(f"\nTitle: {job['title']}")
                print(f"Company: {job['company']}")
                print(f"Link: {job['link']}")
                print(f"Scraped at: {job['scrape_time']}")
                print("-" * 50)

if __name__ == "__main__":
    main() 