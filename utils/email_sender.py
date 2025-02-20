import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

class EmailSender:
    def __init__(self, sender_email, sender_password):
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.logger = logging.getLogger(__name__)

    def format_jobs_html(self, jobs, job_title):
        html = f"""
        <html>
            <head>
                <style>
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                    th {{ background-color: #4CAF50; color: white; }}
                    tr:hover {{ background-color: #f5f5f5; }}
                    a {{ color: #0066cc; text-decoration: none; }}
                </style>
            </head>
            <body>
                <h2>LinkedIn Job Alerts - {job_title}</h2>
                <p>Found {len(jobs)} new jobs for {job_title}</p>
                <table>
                    <tr>
                        <th>Title</th>
                        <th>Company</th>
                        <th>Experience</th>
                        <th>Link</th>
                    </tr>
        """
        
        for job in jobs:
            html += f"""
                <tr>
                    <td>{job['title']}</td>
                    <td>{job['company']}</td>
                    <td>{job['experience']}</td>
                    <td><a href="{job['link']}">Apply</a></td>
                </tr>
            """
            
        html += """
                </table>
            </body>
        </html>
        """
        return html

    def send_job_alert(self, recipient_email, jobs_by_title):
        for job_title, jobs in jobs_by_title.items():
            if not jobs:
                self.logger.info(f"No jobs found for {job_title}, skipping email")
                continue

            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'LinkedIn Job Alerts - {job_title}'
            msg['From'] = self.sender_email
            msg['To'] = recipient_email

            html_content = self.format_jobs_html(jobs, job_title)
            msg.attach(MIMEText(html_content, 'html'))

            try:
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(msg)
                self.logger.info(f"Successfully sent email for {job_title} with {len(jobs)} jobs")
            except Exception as e:
                self.logger.error(f"Error sending email for {job_title}: {str(e)}") 