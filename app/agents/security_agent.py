"""
Security Analysis Agent
"""
import os
from crewai import Agent, LLM
from app.config import get_settings

settings = get_settings()

# Set API key for LiteLLM
os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY


def create_security_agent() -> Agent:
    """
    Create an agent specialized in security analysis and vulnerability detection.
    
    This agent focuses on:
    - SQL injection vulnerabilities
    - Cross-site scripting (XSS)
    - Authentication and authorization issues
    - Data exposure and privacy concerns
    - Dependency vulnerabilities
    """
    
    llm = LLM(
        model=f"gemini/{settings.GEMINI_MODEL}",
        temperature=0.1
    )
    
    agent = Agent(
        role="Security Auditor and Vulnerability Specialist",
        goal="Identify security vulnerabilities and potential exploits in code changes",
        backstory="""You are a cybersecurity expert and ethical hacker with extensive 
        experience in application security and penetration testing. You have discovered 
        and responsibly disclosed numerous vulnerabilities in major software systems. 
        Your expertise includes:
        - Identifying SQL injection and NoSQL injection vulnerabilities
        - Detecting Cross-Site Scripting (XSS) and CSRF vulnerabilities
        - Spotting authentication and authorization flaws
        - Finding insecure deserialization and code injection issues
        - Recognizing hardcoded secrets and API keys
        - Identifying insecure cryptographic implementations
        - Detecting path traversal and file inclusion vulnerabilities
        - Finding information disclosure and data leakage issues
        - Spotting insecure dependencies and outdated libraries
        - Recognizing improper input validation and sanitization
        - Identifying race conditions with security implications
        """,
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=3,
    )
    
    return agent
