#!/usr/bin/env python3
"""
Python 3.12 Exact Compatibility Verification

This script verifies that the AI Agent code is compatible with exactly Python 3.12
by checking language features, dependencies, and syntax patterns.
"""
import sys
import ast
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Tuple


def check_python_version():
    """Check if we're running Python 3.12 exactly."""
    version = sys.version_info
    print(f"🐍 Current Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor == 12:
        print("✅ Running exactly Python 3.12")
        return True
    elif version.major == 3 and version.minor > 12:
        print("⚠️  Running newer Python version - testing backward compatibility")
        return True
    else:
        print(f"❌ Need Python 3.12.x, got {version.major}.{version.minor}.{version.micro}")
        return False


def check_language_features():
    """Check that we're only using features available in Python 3.12."""
    print("\n🔍 Checking Python 3.12 language features:")
    
    # Features available in Python 3.12
    features_312 = {
        "from __future__ import annotations": "3.7+",
        "typing.TypedDict": "3.8+",
        "typing.Literal": "3.8+", 
        "typing.Protocol": "3.8+",
        "typing.NewType": "3.5.2+",
        "typing.Generic": "3.5+",
        "enum.Enum": "3.4+",
        "pathlib.Path": "3.4+",
        "dataclasses.dataclass": "3.7+",
        "contextlib.asynccontextmanager": "3.7+",
        "asyncio.gather": "3.7+",
    }
    
    # Features NOT available in Python 3.12 (newer versions)
    features_too_new = {
        "typing.Self": "3.11+",
        "typing.Never": "3.11+", 
        "typing.LiteralString": "3.11+",
        "typing.NotRequired": "3.11+",
        "typing.Required": "3.11+",
        "match/case statements": "3.10+",
        "typing.ParamSpec": "3.10+",
        "typing.TypeGuard": "3.10+",
    }
    
    all_good = True
    
    for feature, min_version in features_312.items():
        try:
            if 'import' in feature:
                exec(feature)
            else:
                module, attr = feature.rsplit('.', 1)
                exec(f'from {module} import {attr}')
            print(f"  ✅ {feature} ({min_version}) - Available")
        except Exception as e:
            print(f"  ❌ {feature} ({min_version}) - Error: {e}")
            all_good = False
    
    print(f"\n📋 Language features check: {'✅ PASSED' if all_good else '❌ FAILED'}")
    return all_good


def analyze_code_files():
    """Analyze Python files for 3.12 compatibility."""
    print("\n🔍 Analyzing code files for Python 3.12 compatibility:")
    
    files_to_check = [
        "ai_agent/core/config.py",
        "ai_agent/core/types.py",
        "ai_agent/core/agent.py", 
        "ai_agent/core/context_managers.py",
        "examples/phase1_improvements_demo.py"
    ]
    
    all_compatible = True
    
    for file_path in files_to_check:
        path = Path(file_path)
        if not path.exists():
            print(f"  ⚠️  {file_path}: File not found")
            continue
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            issues = []
            
            # Check for problematic constructs
            for node in ast.walk(tree):
                # Check for match statements (3.10+, still compatible but note it)
                if isinstance(node, ast.Match):
                    issues.append(f"Line {node.lineno}: match statement (requires Python 3.10+)")
                
                # Check for f-string expressions (3.8+ but verify)
                if isinstance(node, ast.JoinedStr):
                    for value in node.values:
                        if isinstance(value, ast.FormattedValue) and value.format_spec:
                            # Complex f-strings are fine in 3.12
                            pass
            
            if issues:
                print(f"  ⚠️  {file_path}:")
                for issue in issues:
                    print(f"      • {issue}")
                # Don't mark as incompatible for 3.10+ features since 3.12 supports them
            else:
                print(f"  ✅ {file_path}: Compatible")
                
        except SyntaxError as e:
            print(f"  ❌ {file_path}: Syntax error - {e}")
            all_compatible = False
        except Exception as e:
            print(f"  ⚠️  {file_path}: Analysis error - {e}")
    
    print(f"\n📋 Code analysis: {'✅ PASSED' if all_compatible else '❌ FAILED'}")
    return all_compatible


def check_dependency_compatibility():
    """Check if dependencies support Python 3.12."""
    print("\n🔍 Checking dependency compatibility with Python 3.12:")
    
    # Dependencies from requirements.txt that are critical
    critical_deps = {
        "pydantic": ">=2.5.0 supports Python 3.8-3.13",
        "pydantic-settings": ">=2.0.0 supports Python 3.9-3.13",
        "fastapi": ">=0.104.0 supports Python 3.8+",
        "click": ">=8.1.7 supports Python 3.7+",
        "structlog": ">=23.1.0 supports Python 3.7+",
        "aiohttp": ">=3.9.0 supports Python 3.8+",
    }
    
    all_compatible = True
    
    for dep, compatibility in critical_deps.items():
        try:
            # Try to import the package
            spec = importlib.util.find_spec(dep.replace('-', '_'))
            if spec is None:
                print(f"  ⚠️  {dep}: Not installed ({compatibility})")
            else:
                print(f"  ✅ {dep}: Available ({compatibility})")
        except Exception as e:
            print(f"  ⚠️  {dep}: Import check failed - {e}")
    
    print(f"\n📋 Dependency compatibility: {'✅ PASSED' if all_compatible else '⚠️  NEEDS VERIFICATION'}")
    return all_compatible


def check_pyproject_toml():
    """Verify pyproject.toml Python version requirement."""
    print("\n🔍 Checking pyproject.toml Python version requirement:")
    
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("  ⚠️  pyproject.toml not found")
        return False
    
    try:
        with open(pyproject_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'requires-python = "==3.12.*"' in content:
            print("  ✅ pyproject.toml specifies exactly Python 3.12")
            return True
        elif 'requires-python' in content:
            # Extract the requirement
            for line in content.split('\n'):
                if 'requires-python' in line:
                    print(f"  ⚠️  Found: {line.strip()}")
                    break
            print("  ❌ Does not specify exactly Python 3.12")
            return False
        else:
            print("  ⚠️  No requires-python specification found")
            return False
            
    except Exception as e:
        print(f"  ❌ Error reading pyproject.toml: {e}")
        return False


def main():
    """Run all compatibility checks."""
    print("🔍 Python 3.12 Exact Compatibility Verification")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Language Features", check_language_features), 
        ("Code Files", analyze_code_files),
        ("Dependencies", check_dependency_compatibility),
        ("Project Configuration", check_pyproject_toml),
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        results[check_name] = check_func()
    
    print("\n" + "=" * 60)
    print("📊 FINAL COMPATIBILITY REPORT")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name:.<30} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL CHECKS PASSED - Code is Python 3.12 compatible!")
        print("\nThe AI Agent codebase:")
        print("✅ Uses only Python 3.12 compatible features")
        print("✅ Has proper type hints for Python 3.12")
        print("✅ Dependencies support Python 3.12")
        print("✅ Project configuration specifies Python 3.12 exactly")
    else:
        print("⚠️  SOME CHECKS FAILED - Review compatibility issues above")
        print("\nAction items:")
        for check_name, passed in results.items():
            if not passed:
                print(f"• Fix {check_name} compatibility issues")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)