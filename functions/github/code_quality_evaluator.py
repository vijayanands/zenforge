import ast
import radon.complexity as radon
from typing import Dict, List, Union
import re
from pylint import epylint
import tempfile
import os
import difflib
from radon.metrics import h_visit
from radon.raw import analyze

class CodeQualityEvaluator:
    """Evaluates code quality using multiple metrics and static analysis tools."""
    
    def __init__(self):
        self.max_complexity = 10
        self.max_line_length = 100
        self.min_comment_ratio = 0.1

    def evaluate_code_quality(self, code: str, file_path: str = None) -> Dict[str, any]:
        """
        Evaluates Python code quality using multiple metrics.
        
        Args:
            code (str): The Python code to evaluate
            file_path (str): Optional file path for context
            
        Returns:
            Dict containing quality metrics and feedback
        """
        score = 100
        feedback = []
        metrics = {}
        
        try:
            # Parse the code to check for syntax errors
            ast.parse(code)
        except SyntaxError as e:
            return {
                'score': 0,
                'feedback': [f"Syntax error: {str(e)}"],
                'quality_level': 'Failed',
                'metrics': {}
            }

        # Calculate cyclomatic complexity
        try:
            complexity = radon.cc_visit(code)
            max_cc = max([cc.complexity for cc in complexity]) if complexity else 0
            metrics['complexity'] = max_cc
            
            if max_cc > self.max_complexity:
                score -= min(30, (max_cc - self.max_complexity) * 3)
                feedback.append(f"High cyclomatic complexity ({max_cc}). Consider breaking down complex functions.")
        except:
            feedback.append("Unable to calculate complexity")

        # Analyze code metrics using radon
        try:
            hal_metrics = h_visit(code)
            raw_metrics = analyze(code)
            
            metrics.update({
                'loc': raw_metrics.loc,
                'lloc': raw_metrics.lloc,
                'comments': raw_metrics.comments,
                'multi': raw_metrics.multi,
                'blank': raw_metrics.blank
            })
            
            # Check comment ratio
            if raw_metrics.lloc > 0:
                comment_ratio = (raw_metrics.comments + raw_metrics.multi) / raw_metrics.lloc
                metrics['comment_ratio'] = comment_ratio
                
                if comment_ratio < self.min_comment_ratio:
                    score -= 15
                    feedback.append("Insufficient comments. Consider adding more documentation.")
        except:
            feedback.append("Unable to calculate code metrics")

        # Run pylint for additional checks
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_file.flush()
                
                (pylint_stdout, _) = epylint.py_run(temp_file.name, return_std=True)
                pylint_output = pylint_stdout.getvalue()
                
                # Parse pylint output for score
                pylint_score_match = re.search(r'Your code has been rated at (-?\d+\.\d+)', pylint_output)
                if pylint_score_match:
                    pylint_score = float(pylint_score_match.group(1))
                    metrics['pylint_score'] = pylint_score
                    
                    # Adjust score based on pylint rating
                    if pylint_score < 5:
                        score -= 20
                    elif pylint_score < 8:
                        score -= 10
                
                # Extract major issues from pylint output
                major_issues = re.findall(r'([CEF]\d{4}:.*?)(?=\n[A-Z]|\Z)', pylint_output, re.DOTALL)
                if major_issues:
                    feedback.extend([issue.strip() for issue in major_issues[:3]])
                
            os.unlink(temp_file.name)
        except:
            feedback.append("Unable to run pylint analysis")

        # Check line lengths
        long_lines = [i+1 for i, line in enumerate(code.splitlines()) 
                     if len(line.strip()) > self.max_line_length]
        if long_lines:
            score -= min(15, len(long_lines) * 3)
            feedback.append(f"Lines {', '.join(map(str, long_lines[:3]))} exceed {self.max_line_length} characters")

        return {
            'score': max(0, score),
            'feedback': feedback,
            'quality_level': 'Good' if score >= 80 else 'Medium' if score >= 60 else 'Needs Improvement',
            'metrics': metrics
        }

class ContextAwarePREvaluator:
    """Evaluates PR comments in the context of the code changes."""
    
    def evaluate_pr_comment_context(self, 
                                  comment: str, 
                                  old_code: str, 
                                  new_code: str, 
                                  file_path: str = None) -> Dict[str, any]:
        """
        Evaluates PR comment quality considering the code context.
        
        Args:
            comment (str): The PR comment to evaluate
            old_code (str): The original code before changes
            new_code (str): The new code after changes
            file_path (str): Optional file path for context
            
        Returns:
            Dict containing evaluation results and feedback
        """
        score = 100
        feedback = []
        
        # Calculate diff
        diff = list(difflib.unified_diff(
            old_code.splitlines(keepends=True),
            new_code.splitlines(keepends=True),
            fromfile='before',
            tofile='after'
        ))
        
        # Extract changed lines (excluding diff headers)
        changed_lines = [line[1:] for line in diff if line.startswith('+') or line.startswith('-')]
        changed_content = ''.join(changed_lines)
        
        # Check if comment addresses major changes
        major_changes = self._identify_major_changes(old_code, new_code)
        addressed_changes = 0
        
        for change in major_changes:
            if any(keyword in comment.lower() for keyword in change['keywords']):
                addressed_changes += 1
            else:
                feedback.append(f"Comment doesn't address {change['type']}")
        
        if major_changes:
            change_coverage = addressed_changes / len(major_changes)
            score -= int((1 - change_coverage) * 30)
        
        # Check for specific code references
        if len(changed_lines) > 5 and not re.search(r'(line|L)\s*\d+', comment):
            score -= 10
            feedback.append("Consider referencing specific line numbers for large changes")
        
        # Check for technical depth
        if self._has_complex_changes(changed_content) and len(comment) < 100:
            score -= 15
            feedback.append("Complex changes should have more detailed explanations")
        
        # Check for test coverage discussion
        if 'test' in changed_content.lower() or len(changed_lines) > 20:
            if 'test' not in comment.lower():
                score -= 10
                feedback.append("Consider addressing test coverage")
        
        # Check for security implications
        security_keywords = ['auth', 'password', 'token', 'secret', 'credential', 'encrypt']
        if any(keyword in changed_content.lower() for keyword in security_keywords):
            if not any(keyword in comment.lower() for keyword in ['secur', 'risk', 'vulnerab']):
                score -= 15
                feedback.append("Security-related changes should address security implications")
        
        return {
            'score': max(0, score),
            'feedback': feedback,
            'quality_level': 'Good' if score >= 80 else 'Medium' if score >= 60 else 'Needs Improvement',
            'context_coverage': f"{addressed_changes}/{len(major_changes)}" if major_changes else "N/A"
        }
    
    def _identify_major_changes(self, old_code: str, new_code: str) -> List[Dict]:
        """Identifies major types of changes between old and new code."""
        changes = []
        
        # Check for function signature changes
        old_funcs = set(re.findall(r'def\s+(\w+)\s*\(', old_code))
        new_funcs = set(re.findall(r'def\s+(\w+)\s*\(', new_code))
        
        if old_funcs != new_funcs:
            changes.append({
                'type': 'function signature changes',
                'keywords': ['function', 'method', 'signature', 'parameter', 'argument']
            })
        
        # Check for dependency changes
        old_imports = set(re.findall(r'import\s+(\w+)|from\s+(\w+)', old_code))
        new_imports = set(re.findall(r'import\s+(\w+)|from\s+(\w+)', new_code))
        
        if old_imports != new_imports:
            changes.append({
                'type': 'dependency changes',
                'keywords': ['import', 'dependency', 'library', 'module']
            })
        
        # Check for class changes
        if 'class' in new_code:
            changes.append({
                'type': 'class changes',
                'keywords': ['class', 'method', 'attribute', 'property']
            })
        
        return changes
    
    def _has_complex_changes(self, changed_content: str) -> bool:
        """Determines if changes are complex based on heuristics."""
        return any([
            len(changed_content.splitlines()) > 15,
            'class' in changed_content,
            'def' in changed_content,
            'try' in changed_content,
            'async' in changed_content,
            'yield' in changed_content
        ])

# Example usage
def evaluate_code_and_comment(code_before: str, 
                            code_after: str, 
                            pr_comment: str, 
                            file_path: str = None) -> Dict[str, any]:
    """
    Comprehensive evaluation of code changes and PR comment quality.
    
    Args:
        code_before (str): Original code
        code_after (str): Modified code
        pr_comment (str): PR comment to evaluate
        file_path (str): Optional file path for context
        
    Returns:
        Dict containing both code and comment quality evaluations
    """
    code_evaluator = CodeQualityEvaluator()
    pr_evaluator = ContextAwarePREvaluator()
    
    code_quality_before = code_evaluator.evaluate_code_quality(code_before, file_path)
    code_quality_after = code_evaluator.evaluate_code_quality(code_after, file_path)
    comment_quality = pr_evaluator.evaluate_pr_comment_context(
        pr_comment, code_before, code_after, file_path
    )
    
    return {
        'original_code_quality': code_quality_before,
        'modified_code_quality': code_quality_after,
        'quality_delta': code_quality_after['score'] - code_quality_before['score'],
        'comment_quality': comment_quality
    }

# Example usage
