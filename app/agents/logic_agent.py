"""
Logic and Correctness Analysis Agent
"""
import os
from crewai import Agent, LLM
from app.config import get_settings

settings = get_settings()

# Set API key for LiteLLM
os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY


def create_logic_agent() -> Agent:
    """
    Create an agent specialized in analyzing code logic and correctness.
    
    This agent focuses on:
    - Identifying logical errors and bugs
    - Detecting incorrect algorithm implementations
    - Finding edge cases and boundary conditions
    - Spotting potential runtime errors
    """
    
    llm = LLM(
        model=f"gemini/{settings.GEMINI_MODEL}",
        temperature=0.1
    )
    
    agent = Agent(
        role="Senior Code Logic Analyst",
        goal="Identify logical errors, bugs, and potential runtime issues in code changes",
        backstory="""You are an expert software engineer with 15+ years of experience 
        in code review and debugging. You have a keen eye for spotting logical errors, 
        edge cases, and potential bugs that others might miss. Your expertise spans 
        multiple programming languages and paradigms. You excel at:
        - Identifying off-by-one errors and boundary conditions
        - Spotting null pointer exceptions and unhandled cases
        - Finding incorrect algorithm implementations
        - Detecting race conditions and concurrency issues
        - Recognizing inefficient or incorrect data structure usage
        """,
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=3,
    )
    
    return agent
