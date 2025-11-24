"""
PR Diff Parser and Analyzer
"""
import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class FileDiff:
    """Represents a file change in a PR"""
    filename: str
    status: str  # added, modified, deleted, renamed
    additions: int
    deletions: int
    patch: Optional[str]
    language: Optional[str]
    
    def get_changed_lines(self) -> List[Dict[str, any]]:
        """Extract changed lines with context"""
        if not self.patch:
            return []
        
        changed_lines = []
        lines = self.patch.split('\n')
        current_line_num = 0
        
        for line in lines:
            if line.startswith('@@'):
                # Parse line numbers from hunk header
                match = re.search(r'\+(\d+)', line)
                if match:
                    current_line_num = int(match.group(1))
            elif line.startswith('+') and not line.startswith('+++'):
                # Addition
                changed_lines.append({
                    'type': 'addition',
                    'line_number': current_line_num,
                    'content': line[1:].strip()
                })
                current_line_num += 1
            elif line.startswith('-') and not line.startswith('---'):
                # Deletion
                changed_lines.append({
                    'type': 'deletion',
                    'line_number': current_line_num,
                    'content': line[1:].strip()
                })
            else:
                # Context line
                current_line_num += 1
        
        return changed_lines


class DiffParser:
    """Parse and analyze PR diffs"""
    
    # File extension to language mapping
    LANGUAGE_MAP = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'React JSX',
        '.tsx': 'React TSX',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.cs': 'C#',
        '.go': 'Go',
        '.rs': 'Rust',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.sql': 'SQL',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.xml': 'XML',
        '.md': 'Markdown',
    }
    
    @staticmethod
    def detect_language(filename: str) -> Optional[str]:
        """Detect programming language from filename"""
        for ext, lang in DiffParser.LANGUAGE_MAP.items():
            if filename.endswith(ext):
                return lang
        return None
    
    @staticmethod
    def parse_files(files_data: List[Dict]) -> List[FileDiff]:
        """Parse file changes from GitHub API response"""
        file_diffs = []
        
        for file in files_data:
            file_diff = FileDiff(
                filename=file['filename'],
                status=file['status'],
                additions=file['additions'],
                deletions=file['deletions'],
                patch=file.get('patch'),
                language=DiffParser.detect_language(file['filename'])
            )
            file_diffs.append(file_diff)
        
        return file_diffs
    
    @staticmethod
    def categorize_changes(file_diffs: List[FileDiff]) -> Dict[str, List[FileDiff]]:
        """Categorize file changes by type"""
        categories = {
            'added': [],
            'modified': [],
            'deleted': [],
            'renamed': []
        }
        
        for file_diff in file_diffs:
            if file_diff.status in categories:
                categories[file_diff.status].append(file_diff)
        
        return categories
    
    @staticmethod
    def get_summary(file_diffs: List[FileDiff]) -> Dict[str, any]:
        """Generate a summary of changes"""
        total_additions = sum(f.additions for f in file_diffs)
        total_deletions = sum(f.deletions for f in file_diffs)
        
        languages = {}
        for file_diff in file_diffs:
            if file_diff.language:
                languages[file_diff.language] = languages.get(file_diff.language, 0) + 1
        
        categories = DiffParser.categorize_changes(file_diffs)
        
        return {
            'total_files': len(file_diffs),
            'total_additions': total_additions,
            'total_deletions': total_deletions,
            'languages': languages,
            'files_added': len(categories['added']),
            'files_modified': len(categories['modified']),
            'files_deleted': len(categories['deleted']),
            'files_renamed': len(categories['renamed']),
        }
    
    @staticmethod
    def format_diff_for_review(file_diffs: List[FileDiff], max_files: int = 10) -> str:
        """Format diff for agent review"""
        output = []
        output.append("## Pull Request Changes Summary\n")
        
        summary = DiffParser.get_summary(file_diffs)
        output.append(f"**Total Files Changed:** {summary['total_files']}")
        output.append(f"**Additions:** +{summary['total_additions']}")
        output.append(f"**Deletions:** -{summary['total_deletions']}")
        output.append(f"\n**Languages Detected:** {', '.join(summary['languages'].keys())}\n")
        
        output.append("\n## File Changes\n")
        
        # Limit number of files to review
        files_to_review = file_diffs[:max_files]
        if len(file_diffs) > max_files:
            output.append(f"(Showing first {max_files} of {len(file_diffs)} files)\n")
        
        for i, file_diff in enumerate(files_to_review, 1):
            output.append(f"\n### {i}. {file_diff.filename}")
            output.append(f"**Status:** {file_diff.status.upper()}")
            output.append(f"**Language:** {file_diff.language or 'Unknown'}")
            output.append(f"**Changes:** +{file_diff.additions} / -{file_diff.deletions}")
            
            if file_diff.patch:
                output.append("\n**Diff:**")
                output.append("```diff")
                # Truncate very long patches
                patch_lines = file_diff.patch.split('\n')
                if len(patch_lines) > 100:
                    output.append('\n'.join(patch_lines[:100]))
                    output.append(f"\n... (truncated, {len(patch_lines) - 100} more lines)")
                else:
                    output.append(file_diff.patch)
                output.append("```")
            output.append("\n" + "="*80)
        
        return '\n'.join(output)
