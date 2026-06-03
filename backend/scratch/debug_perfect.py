import asyncio
import sys
from app.services.ats_service import ats_service

text = (
    "john.doe@example.com 555-123-4567 linkedin.com/in/johndoe\n"
    "Skills: Python, React, SQL\n"
    "Education: University of Technology, B.S. Computer Science\n"
    "Experience:\n"
    "- Developed a microservices architecture that increased performance by 40%\n"
    "- Managed a team of 15 engineers and streamlined deployments\n"
    "- Created an automated testing pipeline, reducing bugs by 30%\n"
    "This is some extra text to make sure the word count is over 150 words. " * 20
)

result = ats_service._analyze_text(text)
print("SCORE:", result["ats_score"])
print("WEAKNESSES:", result["weaknesses"])
