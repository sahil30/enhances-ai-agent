#!/usr/bin/env python3

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional
import click
from ..core.agent import AIAgent
from ..core.config import load_config


@click.group()
def cli():
    """AI Agent for querying Confluence, JIRA, and code repositories"""
    pass


@cli.command()
@click.option('--config-file', help='Path to configuration file')
def interactive(config_file):
    """Launch interactive problem-solving mode"""
    try:
        from .interactive_cli import InteractiveProblemSolver
        
        click.echo("🚀 Starting AI Agent Interactive Mode...")
        solver = InteractiveProblemSolver()
        asyncio.run(solver.start_session())
        
    except Exception as e:
        click.echo(f"❌ Error starting interactive mode: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('query')
@click.option('--no-confluence', is_flag=True, help='Skip Confluence search')
@click.option('--no-jira', is_flag=True, help='Skip JIRA search')  
@click.option('--no-code', is_flag=True, help='Skip code repository search')
@click.option('--file-types', multiple=True, help='Specify file types to search (java, python, json, shell)')
@click.option('--max-results', default=10, help='Maximum results per source')
@click.option('--jira-key-prefixes', multiple=True, help='Filter JIRA issues by key prefixes (e.g., RNDPLAN, RNDDEV)')
@click.option('--confluence-spaces', multiple=True, help='Filter Confluence search to specific spaces')
@click.option('--output-format', default='text', type=click.Choice(['text', 'json']), help='Output format')
@click.option('--save-to', help='Save results to file')
async def search(query: str, no_confluence: bool, no_jira: bool, no_code: bool, 
                file_types: tuple, max_results: int, jira_key_prefixes: tuple, 
                confluence_spaces: tuple, output_format: str, save_to: Optional[str]):
    """Search for information across Confluence, JIRA, and code repository"""
    
    try:
        # Load configuration
        config = load_config()
        agent = AIAgent(config)
        
        # Set search options
        search_options = {
            "search_confluence": not no_confluence,
            "search_jira": not no_jira,
            "search_code": not no_code,
            "max_results": max_results,
            "file_types": list(file_types) if file_types else None
        }
        
        # Add JIRA key prefix filtering
        if jira_key_prefixes:
            search_options["jira_key_prefixes"] = list(jira_key_prefixes)
        
        # Add Confluence space filtering
        if confluence_spaces:
            search_options["confluence_spaces"] = list(confluence_spaces)
        
        click.echo(f"🔍 Searching for: {query}")
        
        # Process query
        result = await agent.process_query(query, search_options)
        
        # Format output
        if output_format == 'json':
            output = json.dumps(result, indent=2, default=str)
        else:
            output = _format_text_output(result)
        
        # Save or display results
        if save_to:
            Path(save_to).write_text(output)
            click.echo(f"✅ Results saved to {save_to}")
        else:
            click.echo(output)
        
        await agent.close()
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('item_type', type=click.Choice(['confluence', 'jira', 'code']))
@click.argument('item_id')
@click.option('--output-format', default='text', type=click.Choice(['text', 'json']), help='Output format')
async def details(item_type: str, item_id: str, output_format: str):
    """Get detailed information about a specific item"""
    
    try:
        config = load_config()
        agent = AIAgent(config)
        
        click.echo(f"📋 Getting details for {item_type}: {item_id}")
        
        result = await agent.get_detailed_info(item_type, item_id)
        
        if output_format == 'json':
            output = json.dumps(result, indent=2, default=str)
        else:
            output = _format_details_output(result, item_type)
        
        click.echo(output)
        
        await agent.close()
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--repo-path', help='Path to code repository')
def analyze_repo(repo_path: Optional[str]):
    """Analyze code repository structure"""
    
    try:
        from code_reader import CodeRepositoryReader
        
        if not repo_path:
            repo_path = load_config().code_repo_path
        
        reader = CodeRepositoryReader(repo_path)
        
        click.echo(f"📊 Analyzing repository at: {repo_path}")
        
        # Get all files
        all_files = reader._get_all_files()
        
        # Group by file type
        file_types = {}
        for file_path in all_files:
            file_type = reader._get_file_type(file_path)
            if file_type not in file_types:
                file_types[file_type] = []
            file_types[file_type].append(file_path)
        
        # Display statistics
        click.echo(f"\n📈 Repository Statistics:")
        click.echo(f"Total files: {len(all_files)}")
        
        for file_type, files in file_types.items():
            click.echo(f"{file_type.capitalize()}: {len(files)} files")
        
        # Show recent files
        recent_files = sorted(all_files, key=lambda x: x.stat().st_mtime, reverse=True)[:10]
        
        click.echo(f"\n📅 Recently modified files:")
        for file_path in recent_files:
            relative_path = file_path.relative_to(Path(repo_path))
            click.echo(f"  {relative_path}")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def config_check():
    """Check configuration and connectivity"""
    
    try:
        config = load_config()
        
        click.echo("🔧 Checking configuration...")
        
        # Check required environment variables
        required_vars = [
            'CUSTOM_AI_API_URL',
            'CUSTOM_AI_API_KEY', 
            'CONFLUENCE_ACCESS_TOKEN',
            'JIRA_ACCESS_TOKEN'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(config, var.lower(), None):
                missing_vars.append(var)
        
        if missing_vars:
            click.echo(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            click.echo("Please set these in your .env file")
        else:
            click.echo("✅ All required environment variables are set")
        
        # Check code repository path
        if Path(config.code_repo_path).exists():
            click.echo(f"✅ Code repository path exists: {config.code_repo_path}")
        else:
            click.echo(f"⚠️  Code repository path not found: {config.code_repo_path}")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


def _format_text_output(result: dict) -> str:
    """Format search results as readable text"""
    lines = []
    
    lines.append(f"🔍 Query: {result['query']}")
    lines.append("=" * 50)
    
    if 'error' in result:
        lines.append(f"❌ Error: {result['error']}")
        return '\n'.join(lines)
    
    # Solution
    lines.append("💡 AI-Generated Solution:")
    lines.append(result['solution'])
    lines.append("")
    
    # Sources
    sources = result.get('sources', {})
    
    if sources.get('confluence', {}).get('count', 0) > 0:
        lines.append("📚 Confluence Documentation:")
        for doc in sources['confluence']['data']:
            lines.append(f"  • {doc.get('title', 'Unknown')}")
            lines.append(f"    URL: {doc.get('url', 'N/A')}")
            lines.append(f"    Excerpt: {doc.get('excerpt', 'N/A')[:100]}...")
            lines.append("")
    
    if sources.get('jira', {}).get('count', 0) > 0:
        lines.append("🎫 JIRA Issues:")
        for issue in sources['jira']['data']:
            lines.append(f"  • {issue.get('key', 'Unknown')}: {issue.get('summary', 'N/A')}")
            lines.append(f"    Status: {issue.get('status', 'N/A')}")
            lines.append(f"    URL: {issue.get('url', 'N/A')}")
            lines.append("")
    
    if sources.get('code', {}).get('count', 0) > 0:
        lines.append("💻 Code Files:")
        for code in sources['code']['data']:
            lines.append(f"  • {code.get('file_path', 'Unknown')} ({code.get('file_type', 'unknown')})")
            if 'matches' in code:
                lines.append(f"    Matches: {len(code['matches'])}")
                if code['matches']:
                    lines.append(f"    First match: Line {code['matches'][0].get('line_number', 'N/A')}")
            lines.append("")
    
    return '\n'.join(lines)


def _format_details_output(result: dict, item_type: str) -> str:
    """Format detailed item information"""
    lines = []
    
    if 'error' in result:
        return f"❌ Error: {result['error']}"
    
    if item_type == 'confluence':
        lines.append(f"📚 Confluence Page: {result.get('title', 'Unknown')}")
        lines.append(f"Space: {result.get('space', {}).get('name', 'N/A')}")
        lines.append(f"Last Modified: {result.get('version', {}).get('when', 'N/A')}")
        lines.append("Content:")
        lines.append(result.get('body', {}).get('storage', {}).get('value', 'No content')[:1000])
    
    elif item_type == 'jira':
        fields = result.get('fields', {})
        lines.append(f"🎫 JIRA Issue: {result.get('key', 'Unknown')}")
        lines.append(f"Summary: {fields.get('summary', 'N/A')}")
        lines.append(f"Status: {fields.get('status', {}).get('name', 'N/A')}")
        lines.append(f"Priority: {fields.get('priority', {}).get('name', 'N/A')}")
        lines.append(f"Assignee: {fields.get('assignee', {}).get('displayName', 'Unassigned')}")
        lines.append("Description:")
        lines.append(fields.get('description', 'No description')[:1000])
    
    elif item_type == 'code':
        lines.append(f"💻 Code File: {result.get('file_path', 'Unknown')}")
        lines.append(f"Type: {result.get('file_type', 'unknown')}")
        lines.append(f"Size: {result.get('size', 0)} bytes")
        lines.append(f"Lines: {result.get('lines', 0)}")
        if 'analysis' in result:
            lines.append("Analysis:")
            lines.append(json.dumps(result['analysis'], indent=2))
        lines.append("Content:")
        lines.append(result.get('content', 'No content')[:2000])
    
    return '\n'.join(lines)


def main():
    """Main entry point"""
    # Handle async commands
    if len(sys.argv) > 1 and sys.argv[1] in ['search', 'details']:
        asyncio.run(cli())
    else:
        cli()


if __name__ == '__main__':
    main()