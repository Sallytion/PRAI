"""
PR Review Generator using CrewAI Multi-Agent System
"""
from typing import Dict, List
from crewai import Crew, Task, Process
from app.agents import (
    create_logic_agent,
    create_readability_agent,
    create_performance_agent,
    create_security_agent
)
from app.core.diff_parser import DiffParser, FileDiff
import time


class ReviewGenerator:
    """Generate comprehensive PR reviews using multi-agent system"""
    
    def __init__(self):
        self.logic_agent = create_logic_agent()
        self.readability_agent = create_readability_agent()
        self.performance_agent = create_performance_agent()
        self.security_agent = create_security_agent()
    
    def generate_review(self, pr_data: Dict, files_data: List[Dict]) -> Dict:
        """
        Generate a comprehensive review for a pull request.
        
        Args:
            pr_data: Pull request metadata
            files_data: List of changed files with diffs
        
        Returns:
            Dictionary containing review results from all agents
        """
        start_time = time.time()
        
        # Parse diffs
        file_diffs = DiffParser.parse_files(files_data)
        diff_summary = DiffParser.format_diff_for_review(file_diffs)
        
        # Create context for agents
        pr_context = f"""
# Pull Request Information

**Title:** {pr_data.get('title', 'N/A')}
**Author:** {pr_data.get('author', 'N/A')}
**Number:** #{pr_data.get('number', 'N/A')}

**Description:**
{pr_data.get('description', 'No description provided')}

**Statistics:**
- Files Changed: {pr_data.get('changed_files', 0)}
- Additions: +{pr_data.get('additions', 0)}
- Deletions: -{pr_data.get('deletions', 0)}

---

{diff_summary}
"""
        
        # Define tasks for each agent
        tasks = self._create_tasks(pr_context)
        
        # Create and execute crew
        crew = Crew(
            agents=[
                self.logic_agent,
                self.readability_agent,
                self.performance_agent,
                self.security_agent
            ],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        
        # Execute review
        result = crew.kickoff()
        
        execution_time = time.time() - start_time
        
        # Parse and structure results
        structured_results = self._structure_results(result, tasks)
        structured_results['execution_time_seconds'] = int(execution_time)
        structured_results['pr_summary'] = {
            'title': pr_data.get('title'),
            'number': pr_data.get('number'),
            'files_changed': len(file_diffs),
            'total_additions': sum(f.additions for f in file_diffs),
            'total_deletions': sum(f.deletions for f in file_diffs),
        }
        
        return structured_results
    
    def _create_tasks(self, pr_context: str) -> List[Task]:
        """Create tasks for each specialized agent"""
        
        logic_task = Task(
            description=f"""
Analyze the pull request for logical correctness and potential bugs.

{pr_context}

Your analysis should focus on:
1. Logical errors and incorrect implementations
2. Potential runtime errors and exceptions
3. Edge cases and boundary conditions
4. Null/undefined handling issues
5. Incorrect algorithm implementations
6. Race conditions or concurrency issues

Provide specific, actionable feedback with:
- File name and line number references
- Clear description of the issue
- Severity level (Critical, High, Medium, Low)
- Suggested fix or improvement
""",
            expected_output="""A structured analysis containing:
- List of logical issues found (with severity, location, description, and suggestions)
- Overall assessment of code logic quality
- Critical issues that must be addressed before merging
Format the output as a clear, organized report.""",
            agent=self.logic_agent
        )
        
        readability_task = Task(
            description=f"""
Review the pull request for code quality, readability, and maintainability.

{pr_context}

Your review should focus on:
1. Naming conventions (variables, functions, classes)
2. Code organization and structure
3. Code duplication and DRY violations
4. Comment quality and documentation
5. Complexity and cognitive load
6. Adherence to style guides and best practices
7. Design pattern usage

Provide specific, constructive feedback with:
- File name and line number references
- Clear explanation of the issue
- Severity level (Critical, High, Medium, Low)
- Recommended improvements
""",
            expected_output="""A structured review containing:
- List of readability and quality issues (with severity, location, description, and recommendations)
- Overall code quality score (Excellent, Good, Fair, Needs Improvement)
- Suggestions for improving maintainability
Format the output as a clear, organized report.""",
            agent=self.readability_agent,
            context=[logic_task]
        )
        
        performance_task = Task(
            description=f"""
Analyze the pull request for performance issues and optimization opportunities.

{pr_context}

Your analysis should focus on:
1. Algorithmic complexity (time and space)
2. Inefficient operations and bottlenecks
3. Database query optimization
4. Memory leaks and resource management
5. Unnecessary computations
6. Caching opportunities
7. Async/await usage where applicable

Provide specific, performance-focused feedback with:
- File name and line number references
- Performance impact description
- Severity level (Critical, High, Medium, Low)
- Optimization suggestions with expected improvements
""",
            expected_output="""A structured performance analysis containing:
- List of performance issues (with severity, location, impact, and optimization suggestions)
- Overall performance assessment
- Priority optimizations that should be implemented
Format the output as a clear, organized report.""",
            agent=self.performance_agent,
            context=[logic_task, readability_task]
        )
        
        security_task = Task(
            description=f"""
Perform a security audit of the pull request to identify vulnerabilities.

{pr_context}

Your audit should focus on:
1. SQL/NoSQL injection vulnerabilities
2. Cross-Site Scripting (XSS) and CSRF
3. Authentication and authorization flaws
4. Input validation and sanitization
5. Hardcoded secrets and sensitive data exposure
6. Insecure cryptography
7. Dependency vulnerabilities
8. Path traversal and file inclusion issues
9. Information disclosure

Provide specific, security-focused feedback with:
- File name and line number references
- Vulnerability description and exploit potential
- Severity level (Critical, High, Medium, Low)
- Remediation steps and secure alternatives
""",
            expected_output="""A structured security audit containing:
- List of security vulnerabilities (with severity, location, description, and remediation)
- Overall security risk assessment
- Critical vulnerabilities that must be fixed immediately
Format the output as a clear, organized report.""",
            agent=self.security_agent,
            context=[logic_task, readability_task, performance_task]
        )
        
        return [logic_task, readability_task, performance_task, security_task]
    
    def _structure_results(self, crew_result, tasks: List[Task]) -> Dict:
        """Structure the results from crew execution"""
        
        # Extract individual task outputs
        results = {
            'logic_analysis': {
                'report': str(tasks[0].output) if hasattr(tasks[0], 'output') else str(crew_result),
                'agent': 'Logic Analyzer'
            },
            'readability_analysis': {
                'report': str(tasks[1].output) if hasattr(tasks[1], 'output') else '',
                'agent': 'Readability Specialist'
            },
            'performance_analysis': {
                'report': str(tasks[2].output) if hasattr(tasks[2], 'output') else '',
                'agent': 'Performance Expert'
            },
            'security_analysis': {
                'report': str(tasks[3].output) if hasattr(tasks[3], 'output') else '',
                'agent': 'Security Auditor'
            }
        }
        
        # Generate overall summary
        results['overall_summary'] = self._generate_overall_summary(results)
        results['severity'] = self._determine_severity(results)
        results['recommendations'] = self._extract_recommendations(results)
        
        return results
    
    def _generate_overall_summary(self, results: Dict) -> str:
        """Generate an overall summary from all agent reports"""
        summary_parts = [
            "# 🤖 Automated Code Review Summary",
            "\n## Agent Analyses Completed:\n"
        ]
        
        for key in ['logic_analysis', 'readability_analysis', 'performance_analysis', 'security_analysis']:
            if results.get(key, {}).get('report'):
                agent_name = results[key]['agent']
                summary_parts.append(f"✅ **{agent_name}** - Analysis complete")
        
        summary_parts.append("\n## Review Status")
        summary_parts.append("All specialized agents have completed their analysis. Please review the detailed findings below.")
        
        return '\n'.join(summary_parts)
    
    def _determine_severity(self, results: Dict) -> str:
        """Determine overall severity from all analyses"""
        # Check for critical/high severity keywords in reports
        all_reports = ' '.join([
            results.get('logic_analysis', {}).get('report', ''),
            results.get('readability_analysis', {}).get('report', ''),
            results.get('performance_analysis', {}).get('report', ''),
            results.get('security_analysis', {}).get('report', '')
        ]).lower()
        
        if 'critical' in all_reports:
            return 'critical'
        elif 'high' in all_reports or 'severe' in all_reports:
            return 'high'
        elif 'medium' in all_reports or 'moderate' in all_reports:
            return 'medium'
        elif 'low' in all_reports:
            return 'low'
        else:
            return 'info'
    
    def _extract_recommendations(self, results: Dict) -> List[str]:
        """Extract key recommendations from all analyses"""
        recommendations = []
        
        # This is a simplified version - in production, you'd parse structured output
        for analysis_type in ['logic_analysis', 'readability_analysis', 'performance_analysis', 'security_analysis']:
            report = results.get(analysis_type, {}).get('report', '')
            if 'critical' in report.lower():
                recommendations.append(f"Address critical issues found in {analysis_type.replace('_', ' ')}")
        
        if not recommendations:
            recommendations.append("No critical issues found. Review detailed reports for improvements.")
        
        return recommendations
    
    def format_review_comment(self, review_results: Dict) -> str:
        """Format the review results as a GitHub comment"""
        
        comment_parts = []
        
        # Header
        comment_parts.append("# 🤖 PRAI Automated Code Review\n")
        
        # Summary
        comment_parts.append(review_results.get('overall_summary', ''))
        comment_parts.append("\n---\n")
        
        # Severity Badge
        severity = review_results.get('severity', 'info')
        severity_emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢',
            'info': '🔵'
        }
        comment_parts.append(f"## Overall Severity: {severity_emoji.get(severity, '🔵')} {severity.upper()}\n")
        
        # Individual Agent Reports
        analyses = [
            ('logic_analysis', '🧠 Logic & Correctness Analysis'),
            ('readability_analysis', '📖 Code Quality & Readability'),
            ('performance_analysis', '⚡ Performance Analysis'),
            ('security_analysis', '🔒 Security Audit')
        ]
        
        for key, title in analyses:
            if review_results.get(key, {}).get('report'):
                comment_parts.append(f"\n## {title}\n")
                comment_parts.append(review_results[key]['report'])
                comment_parts.append("\n---\n")
        
        # Recommendations
        if review_results.get('recommendations'):
            comment_parts.append("\n## 📋 Key Recommendations\n")
            for i, rec in enumerate(review_results['recommendations'], 1):
                comment_parts.append(f"{i}. {rec}")
        
        # Footer
        comment_parts.append(f"\n\n---")
        comment_parts.append(f"*Review completed in {review_results.get('execution_time_seconds', 0)} seconds*")
        comment_parts.append(f"\n*Powered by PRAI Multi-Agent System*")
        
        return '\n'.join(comment_parts)
