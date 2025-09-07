"""
Interactive CLI for AI Agent with Guided Problem Solving

Provides an interactive command-line interface that guides users through
problem analysis and provides comprehensive solutions by integrating
Confluence, JIRA, and code repository data.
"""

import asyncio
import click
from typing import Dict, List, Any, Optional
import structlog
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import track
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.syntax import Syntax
import json

from ..core.agent import AIAgent
from ..core.config import load_config

logger = structlog.get_logger(__name__)
console = Console()


class InteractiveProblemSolver:
    """Interactive problem solver with guided workflow"""
    
    def __init__(self):
        self.config = load_config()
        self.agent = None
    
    async def start_session(self):
        """Start interactive problem-solving session"""
        
        console.print(Panel.fit(
            "[bold blue]🤖 AI Agent Interactive Problem Solver[/bold blue]\n"
            "I'll help you analyze problems by searching through your:\n"
            "• 📚 Confluence documentation\n"
            "• 🎫 JIRA issues\n"
            "• 💻 Code repository\n\n"
            "Then provide comprehensive solutions with implementation steps.",
            title="Welcome",
            border_style="blue"
        ))
        
        try:
            # Initialize agent
            console.print("🔄 Initializing AI agent...")
            self.agent = AIAgent(self.config)
            
            while True:
                console.print("\n" + "="*60)
                choice = self._main_menu()
                
                if choice == "1":
                    await self._guided_problem_solving()
                elif choice == "2":
                    await self._quick_search()
                elif choice == "3":
                    await self._browse_sources()
                elif choice == "4":
                    await self._view_history()
                elif choice == "5":
                    self._show_help()
                elif choice == "6":
                    break
                else:
                    console.print("[red]Invalid choice. Please try again.[/red]")
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted by user.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
        finally:
            if self.agent:
                await self.agent.close()
                console.print("✅ Session closed successfully.")
    
    def _main_menu(self) -> str:
        """Display main menu and get user choice"""
        
        console.print(Panel(
            "[bold]Choose an option:[/bold]\n\n"
            "1. 🎯 Guided Problem Solving (Recommended)\n"
            "2. 🔍 Quick Search\n"
            "3. 📂 Browse Sources\n"
            "4. 📈 View Search History\n"
            "5. ❓ Help\n"
            "6. 🚪 Exit",
            title="Main Menu",
            border_style="green"
        ))
        
        return Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5", "6"], default="1")
    
    async def _guided_problem_solving(self):
        """Guided problem-solving workflow"""
        
        console.print(Panel.fit(
            "[bold green]🎯 Guided Problem Solving[/bold green]\n"
            "I'll help you analyze your problem step by step.",
            border_style="green"
        ))
        
        # Step 1: Problem description
        problem_description = self._get_problem_description()
        
        # Step 2: Problem analysis preview
        console.print("\n🔍 Analyzing your problem...")
        problem_analysis = await self._preview_problem_analysis(problem_description)
        
        # Step 3: Confirm search strategy
        search_strategy = self._confirm_search_strategy(problem_analysis)
        
        # Step 4: Execute comprehensive search
        console.print("\n🚀 Searching across all sources...")
        result = await self._execute_comprehensive_search(problem_description, search_strategy)
        
        # Step 5: Present results
        await self._present_comprehensive_results(result)
        
        # Step 6: Follow-up options
        await self._follow_up_options(result)
    
    def _get_problem_description(self) -> str:
        """Get detailed problem description from user"""
        
        console.print("\n📝 [bold]Describe your problem:[/bold]")
        console.print("Be as specific as possible. Include:")
        console.print("• What you're trying to do")
        console.print("• What's not working")
        console.print("• Any error messages")
        console.print("• Technologies involved")
        
        console.print("\n[yellow]Enter your problem description (press Enter twice when finished):[/yellow]")
        lines = []
        while True:
            line = input()
            if line.strip() == "" and len(lines) > 0 and lines[-1].strip() == "":
                lines = lines[:-1]  # Remove the last empty line
                break
            lines.append(line)
        problem = "\n".join(lines).strip()
        
        # Optional: Ask for additional context
        if Confirm.ask("\nWould you like to provide additional context?", default=False):
            context_questions = [
                "When did this problem start?",
                "What environment (dev/staging/prod)?",
                "Any recent changes?",
                "Impact on users/systems?"
            ]
            
            additional_context = []
            for question in context_questions:
                answer = Prompt.ask(f"• {question} (optional)", default="")
                if answer.strip():
                    additional_context.append(f"{question}: {answer}")
            
            if additional_context:
                problem += "\n\nAdditional context:\n" + "\n".join(additional_context)
        
        return problem
    
    async def _preview_problem_analysis(self, problem: str) -> Dict[str, Any]:
        """Preview problem analysis before search"""
        
        # Get initial analysis from agent
        analysis = await self.agent._analyze_problem(problem)
        
        # Create analysis table
        table = Table(title="Problem Analysis", show_header=True)
        table.add_column("Aspect", style="cyan", no_wrap=True)
        table.add_column("Analysis", style="white")
        
        table.add_row("Category", analysis.get("problem_category", "general"))
        table.add_row("Urgency", self._format_urgency(analysis.get("urgency", "medium")))
        table.add_row("Complexity", self._format_complexity(analysis.get("complexity", "medium")))
        table.add_row("Technical Terms", ", ".join(analysis.get("technical_terms", [])) or "None detected")
        table.add_row("Key Keywords", ", ".join(analysis.get("keywords", [])[:5]) or "None")
        
        console.print(table)
        
        return analysis
    
    def _format_urgency(self, urgency: str) -> str:
        """Format urgency with appropriate styling"""
        colors = {"high": "red", "medium": "yellow", "low": "green"}
        return f"[{colors.get(urgency, 'white')}]{urgency.upper()}[/{colors.get(urgency, 'white')}]"
    
    def _format_complexity(self, complexity: str) -> str:
        """Format complexity with appropriate styling"""
        colors = {"high": "red", "medium": "yellow", "low": "green"}
        return f"[{colors.get(complexity, 'white')}]{complexity.upper()}[/{colors.get(complexity, 'white')}]"
    
    def _confirm_search_strategy(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Allow user to confirm or modify search strategy"""
        
        # Get recommended strategy
        strategy = self.agent._determine_search_strategy(analysis)
        
        console.print("\n📋 [bold]Recommended Search Strategy:[/bold]")
        
        strategy_table = Table(show_header=True)
        strategy_table.add_column("Source", style="cyan")
        strategy_table.add_column("Enabled", style="white")
        strategy_table.add_column("Max Results", style="white")
        
        strategy_table.add_row(
            "Confluence (Documentation)", 
            "✅ Yes" if strategy.get("search_confluence") else "❌ No",
            str(strategy.get("max_results", 10))
        )
        strategy_table.add_row(
            "JIRA (Issues)", 
            "✅ Yes" if strategy.get("search_jira") else "❌ No",
            str(strategy.get("max_results", 10))
        )
        strategy_table.add_row(
            "Code Repository", 
            "✅ Yes" if strategy.get("search_code") else "❌ No",
            str(strategy.get("max_results", 10))
        )
        
        console.print(strategy_table)
        
        if Confirm.ask("\nUse recommended strategy?", default=True):
            return strategy
        
        # Allow customization
        console.print("\n⚙️ [bold]Customize Search Strategy:[/bold]")
        
        strategy["search_confluence"] = Confirm.ask("Search Confluence documentation?", default=strategy.get("search_confluence", True))
        strategy["search_jira"] = Confirm.ask("Search JIRA issues?", default=strategy.get("search_jira", True))
        strategy["search_code"] = Confirm.ask("Search code repository?", default=strategy.get("search_code", True))
        
        max_results = Prompt.ask("Maximum results per source", default=str(strategy.get("max_results", 10)))
        try:
            strategy["max_results"] = int(max_results)
        except ValueError:
            strategy["max_results"] = 10
        
        return strategy
    
    async def _execute_comprehensive_search(self, problem: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive search with progress tracking"""
        
        with console.status("[bold green]🔍 Searching across sources...") as status:
            result = await self.agent.process_query(problem, strategy)
            status.update("[bold green]✅ Search completed!")
        
        return result
    
    async def _present_comprehensive_results(self, result: Dict[str, Any]):
        """Present comprehensive results in a user-friendly format"""
        
        console.print("\n" + "="*60)
        console.print(Panel.fit(
            "[bold green]🎉 Analysis Complete![/bold green]",
            border_style="green"
        ))
        
        # Show problem analysis
        analysis = result.get("problem_analysis", {})
        console.print(f"\n📊 [bold]Problem Category:[/bold] {analysis.get('problem_category', 'general').title()}")
        console.print(f"⏰ [bold]Urgency:[/bold] {self._format_urgency(analysis.get('urgency', 'medium'))}")
        console.print(f"🧠 [bold]Complexity:[/bold] {self._format_complexity(analysis.get('complexity', 'medium'))}")
        
        # Show confidence score
        confidence = result.get("confidence_score", 0.0)
        confidence_color = "green" if confidence > 0.7 else "yellow" if confidence > 0.4 else "red"
        console.print(f"📈 [bold]Confidence Score:[/bold] [{confidence_color}]{confidence:.1%}[/{confidence_color}]")
        
        # Show ranking insights if available
        ranking_insights = result.get("ranking_insights", {})
        if ranking_insights:
            self._show_ranking_insights(ranking_insights)
        
        # Show sources summary
        sources = result.get("sources", {})
        self._show_sources_summary(sources)
        
        # Show main solution
        console.print("\n" + "="*60)
        solution = result.get("solution", "No solution generated")
        console.print(Panel(
            Markdown(solution),
            title="💡 Recommended Solution",
            border_style="blue"
        ))
        
        # Show implementation steps
        steps = result.get("implementation_steps", [])
        if steps:
            self._show_implementation_steps(steps)
        
        # Show risks
        risks = result.get("risk_assessment", [])
        if risks:
            self._show_risk_assessment(risks)
        
        # Show related issues
        related = result.get("related_issues", [])
        if related:
            self._show_related_issues(related)
    
    def _show_ranking_insights(self, ranking_insights: Dict[str, Any]):
        """Show advanced ranking insights"""
        
        console.print("\n🎯 [bold]Ranking Intelligence:[/bold]")
        
        # Show ranking summary
        ranking_summary = ranking_insights.get("ranking_summary", {})
        if ranking_summary:
            insights_table = Table(show_header=True, title="Result Quality Metrics")
            insights_table.add_column("Metric", style="cyan")
            insights_table.add_column("Score", justify="center")
            insights_table.add_column("Assessment", style="dim")
            
            content_rel = ranking_summary.get("average_content_relevance", 0)
            content_assess = "Excellent" if content_rel > 0.8 else "Good" if content_rel > 0.6 else "Fair" if content_rel > 0.4 else "Poor"
            insights_table.add_row("Content Relevance", f"{content_rel:.1%}", content_assess)
            
            recency = ranking_summary.get("average_recency_score", 0)
            recency_assess = "Very Recent" if recency > 0.8 else "Recent" if recency > 0.6 else "Moderate" if recency > 0.4 else "Older"
            insights_table.add_row("Content Recency", f"{recency:.1%}", recency_assess)
            
            quality = ranking_summary.get("average_quality_score", 0)
            quality_assess = "High Quality" if quality > 0.7 else "Good Quality" if quality > 0.5 else "Standard"
            insights_table.add_row("Content Quality", f"{quality:.1%}", quality_assess)
            
            console.print(insights_table)
        
        # Show correlation insights
        correlation_summary = ranking_insights.get("correlation_summary", [])
        if correlation_summary:
            console.print(f"\n🔗 [bold]Cross-Source Correlations:[/bold]")
            for insight in correlation_summary:
                console.print(f"• {insight}")
        
        # Show recommendations
        recommendations = ranking_insights.get("recommendations", [])
        if recommendations:
            console.print(f"\n💡 [bold]Recommendations:[/bold]")
            for rec in recommendations:
                console.print(f"• [yellow]{rec}[/yellow]")
    
    def _show_sources_summary(self, sources: Dict[str, Any]):
        """Show summary of sources found"""
        
        console.print("\n📚 [bold]Sources Found:[/bold]")
        
        sources_table = Table(show_header=True)
        sources_table.add_column("Source", style="cyan")
        sources_table.add_column("Count", justify="center")
        sources_table.add_column("Top Score", justify="center")
        sources_table.add_column("Top Results", style="dim")
        
        for source_name, source_data in sources.items():
            count = source_data.get("count", 0)
            if count > 0:
                data = source_data.get("data", [])
                top_results = []
                for item in data[:3]:  # Show top 3
                    if source_name == "confluence":
                        top_results.append(item.get("title", "N/A"))
                    elif source_name == "jira":
                        top_results.append(f"{item.get('key', 'N/A')}: {item.get('summary', 'N/A')[:50]}...")
                    elif source_name == "code":
                        top_results.append(item.get("file_path", "N/A"))
                
                # Get top ranking score
                top_score = "N/A"
                if data and len(data) > 0:
                    first_item_score = data[0].get("ranking_score", 0)
                    if first_item_score > 0:
                        top_score = f"{first_item_score:.1%}"
                        # Add color coding
                        if first_item_score > 0.8:
                            top_score = f"[green]{top_score}[/green]"
                        elif first_item_score > 0.6:
                            top_score = f"[yellow]{top_score}[/yellow]"
                        else:
                            top_score = f"[red]{top_score}[/red]"

                sources_table.add_row(
                    source_name.title(),
                    str(count),
                    top_score,
                    "\n".join(top_results) if top_results else "No details"
                )
            else:
                sources_table.add_row(
                    source_name.title(),
                    "0",
                    "[dim]--[/dim]",
                    "[dim]No results found[/dim]"
                )
        
        console.print(sources_table)
    
    def _show_implementation_steps(self, steps: List[str]):
        """Show implementation steps"""
        
        console.print("\n📋 [bold]Implementation Steps:[/bold]")
        for i, step in enumerate(steps, 1):
            console.print(f"{i}. {step}")
    
    def _show_risk_assessment(self, risks: List[str]):
        """Show risk assessment"""
        
        console.print("\n⚠️ [bold yellow]Risk Assessment:[/bold yellow]")
        for risk in risks:
            console.print(f"• [yellow]{risk}[/yellow]")
    
    def _show_related_issues(self, related: List[str]):
        """Show related issues"""
        
        console.print("\n🔗 [bold]Related Issues to Consider:[/bold]")
        for issue in related:
            console.print(f"• {issue}")
    
    async def _follow_up_options(self, result: Dict[str, Any]):
        """Provide follow-up options"""
        
        console.print("\n" + "="*60)
        console.print("[bold]What would you like to do next?[/bold]")
        
        options = [
            "1. 🔍 Get detailed information about a source",
            "2. 🎯 Refine the search",
            "3. 💾 Save results to file",
            "4. 🔄 Search for related problems",
            "5. 🏠 Return to main menu"
        ]
        
        for option in options:
            console.print(option)
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5"], default="5")
        
        if choice == "1":
            await self._get_detailed_info(result)
        elif choice == "2":
            await self._refine_search(result)
        elif choice == "3":
            self._save_results(result)
        elif choice == "4":
            await self._search_related_problems(result)
        # choice == "5" returns to main menu
    
    async def _get_detailed_info(self, result: Dict[str, Any]):
        """Get detailed information about a specific source"""
        
        sources = result.get("sources", {})
        available_sources = []
        
        for source_name, source_data in sources.items():
            if source_data.get("count", 0) > 0:
                available_sources.append(source_name)
        
        if not available_sources:
            console.print("[yellow]No detailed sources available.[/yellow]")
            return
        
        # Let user choose source type
        console.print("\n📂 [bold]Available Sources:[/bold]")
        for i, source in enumerate(available_sources, 1):
            console.print(f"{i}. {source.title()}")
        
        try:
            choice_idx = int(Prompt.ask("Choose source type", choices=[str(i) for i in range(1, len(available_sources) + 1)])) - 1
            chosen_source = available_sources[choice_idx]
        except (ValueError, IndexError):
            console.print("[red]Invalid choice.[/red]")
            return
        
        # Show available items
        source_data = sources[chosen_source]
        items = source_data.get("data", [])
        
        console.print(f"\n📋 [bold]{chosen_source.title()} Items:[/bold]")
        for i, item in enumerate(items, 1):
            if chosen_source == "confluence":
                console.print(f"{i}. {item.get('title', 'N/A')}")
            elif chosen_source == "jira":
                console.print(f"{i}. {item.get('key', 'N/A')}: {item.get('summary', 'N/A')}")
            elif chosen_source == "code":
                console.print(f"{i}. {item.get('file_path', 'N/A')}")
        
        try:
            item_idx = int(Prompt.ask("Choose item", choices=[str(i) for i in range(1, len(items) + 1)])) - 1
            chosen_item = items[item_idx]
        except (ValueError, IndexError):
            console.print("[red]Invalid choice.[/red]")
            return
        
        # Get detailed info
        console.print("\n🔄 Getting detailed information...")
        
        if chosen_source == "confluence":
            item_id = chosen_item.get("id")
        elif chosen_source == "jira":
            item_id = chosen_item.get("key")
        else:  # code
            item_id = chosen_item.get("file_path")
        
        detailed_info = await self.agent.get_detailed_info(chosen_source, item_id)
        
        # Display detailed info
        if chosen_source == "confluence":
            self._show_confluence_details(detailed_info)
        elif chosen_source == "jira":
            self._show_jira_details(detailed_info)
        else:  # code
            self._show_code_details(detailed_info)
    
    def _show_confluence_details(self, details: Dict[str, Any]):
        """Show detailed Confluence page information"""
        
        console.print(Panel(
            f"[bold]{details.get('title', 'N/A')}[/bold]\n"
            f"Space: {details.get('space', 'N/A')}\n"
            f"Last Modified: {details.get('last_modified', 'N/A')}\n\n"
            f"{details.get('excerpt', 'No excerpt available')[:500]}...",
            title="📄 Confluence Page Details",
            border_style="blue"
        ))
    
    def _show_jira_details(self, details: Dict[str, Any]):
        """Show detailed JIRA issue information"""
        
        console.print(Panel(
            f"[bold]{details.get('key', 'N/A')}: {details.get('summary', 'N/A')}[/bold]\n"
            f"Status: {details.get('status', 'N/A')}\n"
            f"Priority: {details.get('priority', 'N/A')}\n"
            f"Assignee: {details.get('assignee', 'N/A')}\n\n"
            f"{details.get('description', 'No description available')[:500]}...",
            title="🎫 JIRA Issue Details",
            border_style="red"
        ))
    
    def _show_code_details(self, details: Dict[str, Any]):
        """Show detailed code file information"""
        
        file_path = details.get('file_path', 'N/A')
        content = details.get('content', 'No content available')[:1000]
        file_type = details.get('file_type', 'text')
        
        console.print(f"\n📁 [bold]File:[/bold] {file_path}")
        console.print(Panel(
            Syntax(content, file_type, theme="monokai", line_numbers=True),
            title="💻 Code Content",
            border_style="green"
        ))
    
    async def _refine_search(self, original_result: Dict[str, Any]):
        """Allow user to refine their search"""
        
        console.print("\n🎯 [bold]Refine Search[/bold]")
        
        # Get new search parameters
        new_query = Prompt.ask("Enter refined query (or press Enter to keep original)", default="")
        
        if not new_query.strip():
            new_query = original_result.get("query", "")
        
        # Modify search options
        modify_options = Confirm.ask("Modify search options?", default=False)
        
        search_options = {}
        if modify_options:
            search_options["search_confluence"] = Confirm.ask("Search Confluence?", default=True)
            search_options["search_jira"] = Confirm.ask("Search JIRA?", default=True)
            search_options["search_code"] = Confirm.ask("Search code?", default=True)
            
            max_results = Prompt.ask("Max results per source", default="10")
            try:
                search_options["max_results"] = int(max_results)
            except ValueError:
                search_options["max_results"] = 10
        
        # Execute refined search
        console.print("\n🔄 Executing refined search...")
        refined_result = await self.agent.process_query(new_query, search_options)
        
        # Present refined results
        await self._present_comprehensive_results(refined_result)
        await self._follow_up_options(refined_result)
    
    def _save_results(self, result: Dict[str, Any]):
        """Save results to file"""
        
        filename = Prompt.ask("Enter filename", default="ai_agent_results.json")
        
        try:
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            console.print(f"✅ Results saved to {filename}")
        except Exception as e:
            console.print(f"[red]Error saving file: {e}[/red]")
    
    async def _search_related_problems(self, result: Dict[str, Any]):
        """Search for related problems based on current results"""
        
        console.print("\n🔍 [bold]Searching for related problems...[/bold]")
        
        # Generate related queries
        related_queries = await self.agent.suggest_related_queries(
            result.get("query", ""),
            result
        )
        
        if not related_queries:
            console.print("[yellow]No related queries found.[/yellow]")
            return
        
        console.print("\n💡 [bold]Suggested Related Searches:[/bold]")
        for i, query in enumerate(related_queries, 1):
            console.print(f"{i}. {query}")
        
        if Confirm.ask("Execute one of these searches?", default=True):
            try:
                choice_idx = int(Prompt.ask("Choose query", choices=[str(i) for i in range(1, len(related_queries) + 1)])) - 1
                chosen_query = related_queries[choice_idx]
            except (ValueError, IndexError):
                console.print("[red]Invalid choice.[/red]")
                return
            
            # Execute related search
            console.print(f"\n🔄 Searching for: {chosen_query}")
            related_result = await self.agent.process_query(chosen_query)
            
            await self._present_comprehensive_results(related_result)
            await self._follow_up_options(related_result)
    
    async def _quick_search(self):
        """Quick search without guided workflow"""
        
        console.print(Panel.fit(
            "[bold yellow]🔍 Quick Search[/bold yellow]\n"
            "Enter your query for immediate search across all sources.",
            border_style="yellow"
        ))
        
        query = Prompt.ask("Enter your search query")
        
        console.print("\n🚀 Searching...")
        result = await self.agent.process_query(query)
        
        await self._present_comprehensive_results(result)
        await self._follow_up_options(result)
    
    async def _browse_sources(self):
        """Browse available sources"""
        
        console.print(Panel.fit(
            "[bold cyan]📂 Browse Sources[/bold cyan]\n"
            "Explore your available data sources.",
            border_style="cyan"
        ))
        
        console.print("This feature is coming soon!")
        console.print("You'll be able to:")
        console.print("• Browse Confluence spaces")
        console.print("• Browse JIRA projects")
        console.print("• Browse code repository structure")
    
    async def _view_history(self):
        """View search history"""
        
        console.print(Panel.fit(
            "[bold magenta]📈 Search History[/bold magenta]\n"
            "View your recent searches and results.",
            border_style="magenta"
        ))
        
        console.print("Search history feature is coming soon!")
        console.print("You'll be able to:")
        console.print("• View recent searches")
        console.print("• Re-run previous searches")
        console.print("• Compare results over time")
    
    def _show_help(self):
        """Show help information"""
        
        help_content = """
[bold blue]🤖 AI Agent Interactive Help[/bold blue]

[bold]What does this tool do?[/bold]
The AI Agent helps you solve problems by intelligently searching through your:
• Confluence documentation
• JIRA issues and tickets
• Source code repository

It then uses AI to analyze all the found information and provide comprehensive solutions.

[bold]Features:[/bold]
• Intelligent problem categorization
• Multi-source search optimization
• Structured solution generation
• Implementation step guidance
• Risk assessment
• Related issue detection

[bold]Tips for best results:[/bold]
• Be specific about your problem
• Include error messages if applicable
• Mention the technologies involved
• Describe the context (environment, recent changes, etc.)

[bold]Search Strategy:[/bold]
The tool automatically determines the best search strategy based on your problem type:
• Documentation issues → Focus on Confluence
• Bugs/errors → Focus on JIRA and code
• Performance issues → Focus on code and related tickets
• Configuration problems → Search all sources

[bold]Getting Started:[/bold]
1. Use "Guided Problem Solving" for complex issues
2. Use "Quick Search" for simple lookups
3. Always review the problem analysis before searching
4. Explore detailed source information when needed
"""
        
        console.print(Panel(help_content, border_style="blue"))


@click.command()
@click.option('--config-file', help='Path to configuration file')
def interactive_cli(config_file):
    """Launch interactive AI Agent CLI"""
    
    try:
        solver = InteractiveProblemSolver()
        asyncio.run(solver.start_session())
    except Exception as e:
        console.print(f"[red]Failed to start interactive session: {e}[/red]")


if __name__ == "__main__":
    interactive_cli()