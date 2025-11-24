"""
Code Readability and Quality Analysis Agent
"""
import os
from crewai import Agent, LLM
from app.config import get_settings

settings = get_settings()

# Set API key for LiteLLM
os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY


def create_readability_agent() -> Agent:
    """
    Create an agent specialized in code readability and maintainability.
    
    This agent focuses on:
    - Code structure and organization
    - Naming conventions and clarity
    - Documentation and comments
    - Code duplication and DRY principles
    - Design patterns and best practices
    """
    
    llm = LLM(
        model=f"gemini/{settings.GEMINI_MODEL}",
        temperature=0.1
    )
    
    agent = Agent(
        role="Code Quality and Readability Specialist",
        goal="Ensure code is clean, maintainable, and follows best practices",
        backstory="""You are a passionate advocate for clean code and software 
        craftsmanship. With extensive experience in large-scale software projects, 
        you understand the importance of maintainable code. You specialize in:
        - Enforcing clear and consistent naming conventions
        - Identifying code smells and suggesting refactoring opportunities
        - Ensuring proper code organization and modularity
        - Promoting DRY (Don't Repeat Yourself) principles
        - Advocating for appropriate comments and documentation
        - Spotting violations of SOLID principles
        - Recommending appropriate design patterns
        - Ensuring code follows language-specific style guides
        """,
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=3,
    )
    
    return agent
