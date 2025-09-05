import os
import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path


class CodeRepositoryReader:
    """Reader for various code file types in the repository"""
    
    SUPPORTED_EXTENSIONS = {
        '.java': 'java',
        '.py': 'python', 
        '.json': 'json',
        '.sh': 'shell',
        '.bash': 'shell',
        '.zsh': 'shell'
    }
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.file_cache = {}
    
    def search_files(self, query: str, file_types: List[str] = None) -> List[Dict[str, Any]]:
        """Search for files containing the query text"""
        if file_types is None:
            file_types = list(self.SUPPORTED_EXTENSIONS.values())
        
        results = []
        
        for file_path in self._get_all_files():
            if self._get_file_type(file_path) not in file_types:
                continue
            
            try:
                content = self._read_file(file_path)
                if self._contains_query(content, query):
                    result = {
                        'file_path': str(file_path.relative_to(self.repo_path)),
                        'full_path': str(file_path),
                        'file_type': self._get_file_type(file_path),
                        'content_preview': self._get_content_preview(content, query),
                        'matches': self._find_matches(content, query),
                        'size': file_path.stat().st_size,
                        'modified': file_path.stat().st_mtime
                    }
                    results.append(result)
            except Exception as e:
                continue
        
        return sorted(results, key=lambda x: len(x['matches']), reverse=True)
    
    def get_file_content(self, file_path: str) -> Dict[str, Any]:
        """Get full content and metadata for a specific file"""
        full_path = self.repo_path / file_path
        
        if not full_path.exists():
            return {}
        
        try:
            content = self._read_file(full_path)
            file_type = self._get_file_type(full_path)
            
            result = {
                'file_path': file_path,
                'full_path': str(full_path),
                'file_type': file_type,
                'content': content,
                'size': full_path.stat().st_size,
                'modified': full_path.stat().st_mtime,
                'lines': len(content.splitlines())
            }
            
            # Add language-specific analysis
            if file_type == 'java':
                result['analysis'] = self._analyze_java(content)
            elif file_type == 'python':
                result['analysis'] = self._analyze_python(content)
            elif file_type == 'json':
                result['analysis'] = self._analyze_json(content)
            elif file_type == 'shell':
                result['analysis'] = self._analyze_shell(content)
            
            return result
            
        except Exception as e:
            return {'error': str(e)}
    
    def search_by_pattern(self, pattern: str, file_types: List[str] = None) -> List[Dict[str, Any]]:
        """Search files using regex pattern"""
        if file_types is None:
            file_types = list(self.SUPPORTED_EXTENSIONS.values())
        
        try:
            regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        except re.error:
            return []
        
        results = []
        
        for file_path in self._get_all_files():
            if self._get_file_type(file_path) not in file_types:
                continue
            
            try:
                content = self._read_file(file_path)
                matches = regex.findall(content)
                
                if matches:
                    result = {
                        'file_path': str(file_path.relative_to(self.repo_path)),
                        'full_path': str(file_path),
                        'file_type': self._get_file_type(file_path),
                        'pattern_matches': matches[:10],  # Limit matches
                        'match_count': len(matches),
                        'content_preview': self._get_pattern_preview(content, regex)
                    }
                    results.append(result)
            except Exception as e:
                continue
        
        return sorted(results, key=lambda x: x['match_count'], reverse=True)
    
    def _get_all_files(self) -> List[Path]:
        """Get all supported files in the repository"""
        files = []
        
        for root, dirs, filenames in os.walk(self.repo_path):
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'target', 'build']]
            
            for filename in filenames:
                file_path = Path(root) / filename
                if self._is_supported_file(file_path):
                    files.append(file_path)
        
        return files
    
    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if file is supported"""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS
    
    def _get_file_type(self, file_path: Path) -> str:
        """Get file type based on extension"""
        return self.SUPPORTED_EXTENSIONS.get(file_path.suffix.lower(), 'unknown')
    
    def _read_file(self, file_path: Path) -> str:
        """Read file content with caching"""
        if str(file_path) in self.file_cache:
            return self.file_cache[str(file_path)]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.file_cache[str(file_path)] = content
                return content
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
                self.file_cache[str(file_path)] = content
                return content
    
    def _contains_query(self, content: str, query: str) -> bool:
        """Check if content contains query (case-insensitive)"""
        return query.lower() in content.lower()
    
    def _find_matches(self, content: str, query: str) -> List[Dict[str, Any]]:
        """Find all occurrences of query in content"""
        matches = []
        lines = content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            if query.lower() in line.lower():
                matches.append({
                    'line_number': line_num,
                    'line_content': line.strip(),
                    'context': self._get_line_context(lines, line_num - 1, 2)
                })
        
        return matches[:20]  # Limit to 20 matches
    
    def _get_content_preview(self, content: str, query: str) -> str:
        """Get preview of content around the query"""
        lines = content.splitlines()
        
        for i, line in enumerate(lines):
            if query.lower() in line.lower():
                start = max(0, i - 3)
                end = min(len(lines), i + 4)
                preview_lines = lines[start:end]
                return '\n'.join(f"{start + j + 1:4}: {line}" for j, line in enumerate(preview_lines))
        
        return content[:300] + "..." if len(content) > 300 else content
    
    def _get_pattern_preview(self, content: str, regex) -> str:
        """Get preview of content with regex matches"""
        lines = content.splitlines()
        
        for i, line in enumerate(lines):
            if regex.search(line):
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                preview_lines = lines[start:end]
                return '\n'.join(f"{start + j + 1:4}: {line}" for j, line in enumerate(preview_lines))
        
        return content[:300] + "..." if len(content) > 300 else content
    
    def _get_line_context(self, lines: List[str], line_index: int, context_lines: int) -> List[str]:
        """Get context around a specific line"""
        start = max(0, line_index - context_lines)
        end = min(len(lines), line_index + context_lines + 1)
        return lines[start:end]
    
    def _analyze_java(self, content: str) -> Dict[str, Any]:
        """Analyze Java file structure"""
        analysis = {
            'classes': re.findall(r'class\s+(\w+)', content),
            'interfaces': re.findall(r'interface\s+(\w+)', content),
            'methods': re.findall(r'(?:public|private|protected)?\s*\w+\s+(\w+)\s*\(', content),
            'imports': re.findall(r'import\s+([\w.]+);', content),
            'package': re.search(r'package\s+([\w.]+);', content)
        }
        if analysis['package']:
            analysis['package'] = analysis['package'].group(1)
        return analysis
    
    def _analyze_python(self, content: str) -> Dict[str, Any]:
        """Analyze Python file structure"""
        return {
            'classes': re.findall(r'class\s+(\w+)', content),
            'functions': re.findall(r'def\s+(\w+)', content),
            'imports': re.findall(r'(?:from\s+[\w.]+\s+)?import\s+([\w.,\s*]+)', content),
            'docstrings': re.findall(r'"""(.*?)"""', content, re.DOTALL)[:3]  # First 3 docstrings
        }
    
    def _analyze_json(self, content: str) -> Dict[str, Any]:
        """Analyze JSON file structure"""
        try:
            data = json.loads(content)
            return {
                'valid_json': True,
                'keys': list(data.keys()) if isinstance(data, dict) else [],
                'type': type(data).__name__,
                'size': len(content)
            }
        except json.JSONDecodeError:
            return {
                'valid_json': False,
                'error': 'Invalid JSON format'
            }
    
    def _analyze_shell(self, content: str) -> Dict[str, Any]:
        """Analyze shell script structure"""
        return {
            'shebang': content.split('\n')[0] if content.startswith('#!') else None,
            'functions': re.findall(r'(\w+)\s*\(\s*\)\s*{', content),
            'variables': re.findall(r'(\w+)=', content),
            'commands': re.findall(r'^([a-zA-Z][\w-]*)', content, re.MULTILINE)[:20]  # First 20 commands
        }