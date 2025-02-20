from dotenv import load_dotenv
import os
import time
from linkedin_scraper import LinkedInJobScraper
from utils.email_sender import EmailSender
import json
import logging
from datetime import datetime
import sys
import schedule

# Add this line before accessing environment variables
load_dotenv()

def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configure logging
    log_filename = f'logs/linkedin_jobs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def load_config():
    with open('config/metadata.json', 'r') as f:
        return json.load(f)

def job():
    scraper = LinkedInJobScraper()
    try:
        jobs = scraper.run()
        if jobs:
            print(f"Found {sum(len(jobs_list) for jobs_list in jobs.values())} jobs")
    except Exception as e:
        print(f"Error running scraper: {e}")

def main():
    print("Starting the script...")
    # Get the frequency from config
    scraper = LinkedInJobScraper()
    frequency = scraper.config["auto_scrape_frequency_in_mins"]
    
    # Schedule the job
    schedule.every(frequency).minutes.do(job)
    
    # Run the job immediately once
    job()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main() 