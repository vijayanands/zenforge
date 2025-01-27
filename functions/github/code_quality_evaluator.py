import ast
import radon.complexity as radon
from typing import Dict, List, Union
import re
from pylint import lint
import tempfile
import os
import difflib
from radon.metrics import h_visit
from radon.raw import analyze
from pylint.lint import Run
from pylint.reporters import JSONReporter
import io
import sys
from contextlib import redirect_stdout, redirect_stderr


class CodeQualityEvaluator:
    """Evaluates code quality using multiple metrics and static analysis tools."""

    def __init__(self):
        self.max_complexity = 10
        self.max_line_length = 100
        self.min_comment_ratio = 0.1
        self.max_halstead_difficulty = 15

        # File type specific configurations
        self.file_type_configs = {
            'test': {
                'min_comment_ratio': 0.05,  # Less documentation needed for tests
                'max_complexity': 15,  # Test functions can be a bit more complex
            },
            'init': {
                'max_line_length': 120,  # Allow longer lines in __init__.py
                'min_comment_ratio': 0.05,  # Less documentation needed
            },
            'main': {
                'min_comment_ratio': 0.15,  # More documentation needed for main modules
            }
        }

    def _get_file_type(self, file_path: str) -> str:
        """Determines the type of Python file based on its path and name."""
        if not file_path:
            return 'main'

        file_name = os.path.basename(file_path).lower()
        if 'test' in file_name or 'test' in os.path.dirname(file_path).lower():
            return 'test'
        elif file_name == '__init__.py':
            return 'init'
        else:
            return 'main'

    def _adjust_thresholds(self, file_type: str):
        """Adjusts quality thresholds based on file type."""
        if file_type in self.file_type_configs:
            config = self.file_type_configs[file_type]
            self.max_complexity = config.get('max_complexity', self.max_complexity)
            self.max_line_length = config.get('max_line_length', self.max_line_length)
            self.min_comment_ratio = config.get('min_comment_ratio', self.min_comment_ratio)

    def _run_pylint_analysis(self, code: str) -> Dict[str, any]:
        """Run pylint analysis on code"""
        try:
            # Create a temporary file for pylint analysis
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_file.flush()
                temp_path = temp_file.name

            try:
                # Create JSON reporter
                json_reporter = JSONReporter()
                
                # Run pylint with JSON reporter
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    Run(
                        [temp_path],
                        reporter=json_reporter,
                        exit=False
                    )
                
                # Get results
                results = json_reporter.messages
                
                # Calculate score (10 - number of errors/warnings)
                score = 10.0
                feedback = []
                
                for msg in results:
                    if msg.category in ('error', 'warning', 'convention', 'refactor'):
                        score -= 0.5
                        feedback.append(f"{msg.symbol} ({msg.line}:{msg.column}): {msg.msg}")
                
                return {
                    'score': max(0.0, score),
                    'feedback': feedback[:3],  # Return top 3 issues
                    'total_issues': len(results)
                }
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            return {
                'score': 0.0,
                'feedback': [f"Pylint analysis failed: {str(e)}"],
                'total_issues': 0
            }

    def _calculate_halstead_metrics(self, code: str) -> Dict[str, any]:
        """Calculate Halstead metrics for the code"""
        try:
            hal_metrics = h_visit(code)
            if not hal_metrics:
                return None
                
            # Get metrics from the first module
            metrics = hal_metrics[0] if isinstance(hal_metrics, list) else next(iter(hal_metrics))
            
            return {
                'h1': metrics.h1,
                'h2': metrics.h2,
                'N1': metrics.N1,
                'N2': metrics.N2,
                'vocabulary': metrics.vocabulary,
                'length': metrics.length,
                'volume': metrics.volume,
                'difficulty': metrics.difficulty,
                'effort': metrics.effort,
                'time': metrics.time,
                'bugs': metrics.bugs
            }
        except Exception as e:
            return None

    def evaluate_code_quality(self, code: str, file_path: str = None) -> Dict[str, any]:
        """
        Evaluates Python code quality using multiple metrics.

        Args:
            code (str): The Python code to evaluate
            file_path (str): File path for context (affects thresholds and module naming)

        Returns:
            Dict containing quality metrics and feedback
        """
        # Adjust thresholds based on file type
        file_type = self._get_file_type(file_path)
        self._adjust_thresholds(file_type)

        score = 100
        feedback = []
        metrics = {
            'file_type': file_type,
            'file_path': file_path or 'unknown'
        }

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

        # Calculate Halstead metrics
        halstead_results = self._calculate_halstead_metrics(code)
        if halstead_results:
            metrics.update(halstead_results)
            
            if halstead_results['difficulty'] > self.max_halstead_difficulty:
                score -= min(20, (halstead_results['difficulty'] - self.max_halstead_difficulty) * 2)
                feedback.append(f"High code complexity (Halstead difficulty: {halstead_results['difficulty']:.2f})")

            if halstead_results['bugs'] > 0.3:
                score -= min(15, int(halstead_results['bugs'] * 30))
                feedback.append(f"Code might be prone to bugs (Estimated bugs: {halstead_results['bugs']:.2f})")
        else:
            feedback.append("Unable to calculate Halstead metrics")

        # Analyze raw code metrics
        try:
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

        # Run pylint analysis
        try:
            pylint_results = self._run_pylint_analysis(code)
            if pylint_results:
                metrics['pylint_score'] = pylint_results['score']
                
                # Adjust score based on pylint rating
                if pylint_results['score'] < 5:
                    score -= 20
                elif pylint_results['score'] < 8:
                    score -= 10
                    
                # Add pylint feedback
                feedback.extend(pylint_results['feedback'])
        except Exception as e:
            feedback.append(f"Unable to run pylint analysis: {str(e)}")

        # Check line lengths
        long_lines = [i + 1 for i, line in enumerate(code.splitlines())
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
            file_path (str): File path for context (affects evaluation criteria)

        Returns:
            Dict containing evaluation results and feedback
        """
        score = 100
        feedback = []

        # Determine file type and adjust expectations
        is_test_file = file_path and ('test' in file_path.lower() or 'test' in os.path.basename(file_path).lower())
        is_init_file = file_path and os.path.basename(file_path) == '__init__.py'

        # Calculate diff
        diff = list(difflib.unified_diff(
            old_code.splitlines(keepends=True),
            new_code.splitlines(keepends=True),
            fromfile=file_path or 'before',
            tofile=file_path or 'after'
        ))

        # Extract changed lines (excluding diff headers)
        changed_lines = [line[1:] for line in diff if line.startswith('+') or line.startswith('-')]
        changed_content = ''.join(changed_lines)

        # Check if comment addresses major changes
        major_changes = self._identify_major_changes(old_code, new_code, file_path)
        addressed_changes = 0

        for change in major_changes:
            if any(keyword in comment.lower() for keyword in change['keywords']):
                addressed_changes += 1
            else:
                feedback.append(f"Comment doesn't address {change['type']}")

        if major_changes:
            change_coverage = addressed_changes / len(major_changes)
            score -= int((1 - change_coverage) * 30)

        # Adjust expectations based on file type
        if is_test_file:
            # For test files, focus more on test coverage and assertions
            if 'assert' in changed_content and 'assert' not in comment.lower():
                score -= 10
                feedback.append("Consider explaining the new assertions or test cases")
        elif is_init_file:
            # For __init__ files, focus more on API and interface changes
            if 'import' in changed_content and 'import' not in comment.lower():
                score -= 10
                feedback.append("Consider explaining changes to module interface")
        else:
            # Regular file checks
            if len(changed_lines) > 5 and not re.search(r'(line|L)\s*\d+', comment):
                score -= 10
                feedback.append("Consider referencing specific line numbers for large changes")

        # Check for technical depth
        if self._has_complex_changes(changed_content) and len(comment) < 100:
            score -= 15
            feedback.append("Complex changes should have more detailed explanations")

        # Check for test coverage discussion (more important for non-test files)
        if not is_test_file and ('test' in changed_content.lower() or len(changed_lines) > 20):
            if 'test' not in comment.lower():
                score -= 10
                feedback.append("Consider addressing test coverage")

        # Security checks (more important for non-test files)
        if not is_test_file:
            security_keywords = ['auth', 'password', 'token', 'secret', 'credential', 'encrypt']
            if any(keyword in changed_content.lower() for keyword in security_keywords):
                if not any(keyword in comment.lower() for keyword in ['secur', 'risk', 'vulnerab']):
                    score -= 15
                    feedback.append("Security-related changes should address security implications")

        return {
            'score': max(0, score),
            'feedback': feedback,
            'quality_level': 'Good' if score >= 80 else 'Medium' if score >= 60 else 'Needs Improvement',
            'context_coverage': f"{addressed_changes}/{len(major_changes)}" if major_changes else "N/A",
            'file_type': 'test' if is_test_file else 'init' if is_init_file else 'main'
        }

    def _identify_major_changes(self, old_code: str, new_code: str, file_path: str = None) -> List[Dict]:
        """Identifies major types of changes between old and new code."""
        changes = []

        # Adjust change detection based on file type
        is_test_file = file_path and ('test' in file_path.lower() or 'test' in os.path.basename(file_path).lower())
        is_init_file = file_path and os.path.basename(file_path) == '__init__.py'

        # Check for function signature changes
        old_funcs = set(re.findall(r'def\s+(\w+)\s*\(', old_code))
        new_funcs = set(re.findall(r'def\s+(\w+)\s*\(', new_code))

        if old_funcs != new_funcs:
            if is_test_file:
                keywords = ['test', 'assert', 'fixture', 'parameter']
            else:
                keywords = ['function', 'method', 'signature', 'parameter', 'argument']
            changes.append({
                'type': 'function signature changes',
                'keywords': keywords
            })

        # Check for dependency changes (more important in __init__.py)
        old_imports = set(re.findall(r'import\s+(\w+)|from\s+(\w+)', old_code))
        new_imports = set(re.findall(r'import\s+(\w+)|from\s+(\w+)', new_code))

        if old_imports != new_imports:
            importance = 'critical' if is_init_file else 'normal'
            changes.append({
                'type': 'dependency changes',
                'keywords': ['import', 'dependency', 'library', 'module'],
                'importance': importance
            })

        # Check for class changes
        if 'class' in new_code:
            if is_test_file:
                keywords = ['test class', 'test case', 'fixture']
            else:
                keywords = ['class', 'method', 'attribute', 'property']
            changes.append({
                'type': 'class changes',
                'keywords': keywords
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
if __name__ == "__main__":
    # Simple example that should work with both metrics
    test_code = '''"""Example module for testing code quality metrics.

This module demonstrates a simple factorial calculation with proper
documentation, type hints, and error handling.
"""

def calculate_factorial(n: int) -> int:
    """Calculate the factorial of a number.
    
    Args:
        n: The number to calculate factorial for
        
    Returns:
        The factorial of n
    
    Raises:
        ValueError: If n is negative
    """
    if not isinstance(n, int):
        raise TypeError("Input must be an integer")
    if n < 0:
        raise ValueError("Input must be non-negative")
    if n == 0:
        return 1
    return n * calculate_factorial(n - 1)
'''
    
    evaluator = CodeQualityEvaluator()
    result = evaluator.evaluate_code_quality(test_code)
    
    print("\nCode Quality Analysis Results:")
    print("-" * 40)
    print(f"Overall Score: {result['score']}")
    print(f"Quality Level: {result['quality_level']}")
    
    if result['feedback']:
        print("\nFeedback:")
        for fb in result['feedback']:
            print(f"- {fb}")
    
    if 'metrics' in result:
        print("\nMetrics:")
        for key, value in result['metrics'].items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")