"""
Performance Analysis Agent
"""
import os
from crewai import Agent, LLM
from app.config import get_settings

settings = get_settings()

# Set API key for LiteLLM
os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY


def create_performance_agent() -> Agent:
    """
    Create an agent specialized in performance analysis and optimization.
    
    This agent focuses on:
    - Time complexity analysis
    - Space complexity analysis
    - Identifying performance bottlenecks
    - Database query optimization
    - Memory leaks and resource management
    """
    
    llm = LLM(
        model=f"gemini/{settings.GEMINI_MODEL}",
        temperature=0.1
    )
    
    agent = Agent(
        role="Performance Optimization Expert",
        goal="Identify performance issues and suggest optimizations",
        backstory="""You are a performance engineering specialist with deep 
        knowledge of algorithmic complexity, system architecture, and optimization 
        techniques. You have optimized applications serving millions of users and 
        excel at:
        - Analyzing time and space complexity of algorithms
        - Identifying O(n²) operations that could be O(n) or O(log n)
        - Spotting inefficient database queries and N+1 problems
        - Detecting memory leaks and improper resource management
        - Finding unnecessary computations and redundant operations
        - Recognizing inefficient data structure choices
        - Identifying blocking operations that could be async
        - Suggesting caching opportunities
        - Detecting premature optimization vs. necessary optimization
        """,
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=3,
    )
    
    return agent
