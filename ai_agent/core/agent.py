"""
AI Agent Core Module with Enhanced Type Safety

This module provides the main AIAgent class with comprehensive type hints
and modern Python patterns for better maintainability and IDE support.
"""
from __future__ import annotations

import asyncio
from typing import Dict, List, Any, Optional, Union, AsyncContextManager
from contextlib import asynccontextmanager
from datetime import datetime

from .config import Config, load_config
from .types import (
    QueryString, SearchResponse, ProblemAnalysis, SearchStrategy,
    UserContext, ComprehensiveSolution, BaseSearchResult,
    SourceType, ProblemCategory,
    Urgency, Complexity, ConfidenceScore, AIAgentError,
    SearchError, ConfigProtocol, AIClientProtocol, MCPClientProtocol
)
from .ai_client import CustomAIClient
from ..mcp import ConfluenceMCPClient, JiraMCPClient
from .code_reader import CodeRepositoryReader
from .query_processor import NLPProcessor, QueryType, QueryIntent
from ..infrastructure.semantic_search import enhance_search_results
from ..infrastructure.advanced_ranking import AdvancedRankingEngine
import structlog


class AIAgent:
    """
    Main AI agent that coordinates between Confluence, JIRA, and code repository 
    with intelligent problem analysis and comprehensive type safety.
    
    Supports async context management for proper resource cleanup.
    """
    
    def __init__(self, config: Optional[Config] = None) -> None:
        """
        Initialize the AI Agent with configuration and client dependencies.
        
        Args:
            config: Configuration object. If None, loads from environment.
            
        Raises:
            ConfigurationError: If configuration validation fails
        """
        self.config: Config = config or load_config()
        self._initialized: bool = False
        
        # Type-annotated client instances
        self.ai_client: AIClientProtocol = CustomAIClient(self.config)
        self.confluence_client: MCPClientProtocol = ConfluenceMCPClient(self.config)
        self.jira_client: MCPClientProtocol = JiraMCPClient(self.config)
        self.code_reader: CodeRepositoryReader = CodeRepositoryReader(
            str(self.config.code_repo_path), self.config
        )
        self.nlp_processor: NLPProcessor = NLPProcessor()
        self.ranking_engine: AdvancedRankingEngine = AdvancedRankingEngine(self.config)
        
        # Structured logger
        self.logger: structlog.stdlib.BoundLogger = structlog.get_logger("ai_agent")
    
    async def __aenter__(self) -> AIAgent:
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit with cleanup."""
        await self.close()
    
    async def initialize(self) -> None:
        """
        Initialize all client connections.
        
        Raises:
            MCPConnectionError: If client connections fail
        """
        if self._initialized:
            return
            
        try:
            self.logger.info("Initializing AI Agent connections")
            
            # Initialize clients that require async setup
            if hasattr(self.confluence_client, 'connect'):
                await self.confluence_client.connect()
            if hasattr(self.jira_client, 'connect'):
                await self.jira_client.connect()
                
            self._initialized = True
            self.logger.info("AI Agent initialization completed")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI Agent: {e}")
            raise AIAgentError(f"Initialization failed: {e}") from e
    
    async def process_query(
        self, 
        query: QueryString, 
        search_options: Optional[Dict[str, Any]] = None
    ) -> SearchResponse:
        """
        Intelligently process a problem query and return comprehensive solution proposal.
        
        Args:
            query: User query string to process
            search_options: Optional search configuration overrides
            
        Returns:
            Comprehensive search response with solutions and metadata
            
        Raises:
            SearchError: If query processing fails
            ValidationError: If input validation fails
        """
        # Input validation
        self._validate_query_input(query, search_options)
        
        if not self._initialized:
            await self.initialize()
        
        self.logger.info("Processing query", query=query, has_options=search_options is not None)
        
        try:
            # Analyze the problem using NLP
            problem_analysis = await self._analyze_problem(query)
            
            # Determine optimal search strategy based on problem type
            search_strategy = self._determine_search_strategy(problem_analysis)
            
            # Override with user options if provided
            if search_options:
                search_strategy = self._merge_search_options(search_strategy, search_options)
            
            # Collect data from all relevant sources
            all_data = await self._collect_comprehensive_data(query, search_strategy, problem_analysis)
            
            # Apply advanced ranking to all results
            user_context = self._build_user_context(search_strategy, problem_analysis)
            ranked_data = self.ranking_engine.rank_all_results(all_data, query, user_context)
            
            # Synthesize comprehensive solution using ranked data
            solution_synthesis = await self._synthesize_solution(query, problem_analysis, ranked_data)
            
            # Build comprehensive response
            response: SearchResponse = {
                "query": query,
                "problem_analysis": problem_analysis,
                "solution": solution_synthesis,
                "sources": ranked_data["sources"],
                "search_strategy": search_strategy,
                "ranking_insights": ranked_data.get("ranking_insights", {}),
                "cross_correlations": ranked_data.get("cross_correlations", []),
                "metadata": {
                    "processing_time": datetime.now().isoformat(),
                    "agent_version": "2.0.0",
                    "total_results": sum(
                        source.get("count", 0) 
                        for source in ranked_data["sources"].values()
                    )
                }
            }
            
            self.logger.info(
                "Query processing completed successfully", 
                confidence=solution_synthesis.get("confidence", 0.0),
                total_results=response["metadata"]["total_results"]
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Query processing failed", error=str(e), query=query)
            raise SearchError(f"Failed to process query: {e}") from e
    
    def _validate_query_input(
        self, 
        query: QueryString, 
        search_options: Optional[Dict[str, Any]]
    ) -> None:
        """
        Validate input parameters for query processing.
        
        Args:
            query: User query string
            search_options: Optional search configuration
            
        Raises:
            ValidationError: If validation fails
        """
        from .types import ValidationError
        
        # Validate query
        if not query or not isinstance(query, str):
            raise ValidationError("Query must be a non-empty string")
        
        query_stripped = query.strip()
        if not query_stripped:
            raise ValidationError("Query cannot be empty or only whitespace")
        
        if len(query_stripped) > 1000:
            raise ValidationError("Query too long (max 1000 characters)")
        
        if len(query_stripped) < 3:
            raise ValidationError("Query too short (min 3 characters)")
        
        # Validate search options if provided
        if search_options is not None:
            if not isinstance(search_options, dict):
                raise ValidationError("search_options must be a dictionary")
            
            # Validate specific option values
            valid_option_keys = {
                'search_confluence', 'search_jira', 'search_code',
                'max_results', 'file_types', 'confluence_spaces',
                'jira_projects', 'jira_key_prefixes'
            }
            
            for key in search_options.keys():
                if key not in valid_option_keys:
                    raise ValidationError(f"Unknown search option: {key}")
            
            # Validate max_results if provided
            max_results = search_options.get('max_results')
            if max_results is not None:
                if not isinstance(max_results, int) or max_results < 1 or max_results > 100:
                    raise ValidationError("max_results must be integer between 1 and 100")
    
    def _merge_search_options(
        self, 
        base_strategy: SearchStrategy, 
        user_options: Dict[str, Any]
    ) -> SearchStrategy:
        """
        Safely merge user options with base search strategy.
        
        Args:
            base_strategy: Base search strategy from problem analysis
            user_options: User-provided option overrides
            
        Returns:
            Merged search strategy
        """
        merged = base_strategy.copy()
        
        # Safe updates with validation
        for key, value in user_options.items():
            if key in merged:
                merged[key] = value  # type: ignore
        
        return merged
    
    async def _analyze_problem(self, query: QueryString) -> ProblemAnalysis:
        """Analyze the problem to understand its nature and determine search strategy"""
        
        try:
            # Use NLP processor to analyze query
            analysis = self.nlp_processor.analyze_query(query)
            
            # Determine problem category
            problem_category = self._categorize_problem(query, analysis)
            
            # Extract key technical terms
            technical_terms = self._extract_technical_terms(query)
            
            # Determine urgency and complexity
            urgency = self._assess_urgency(query)
            complexity = self._assess_complexity(query, technical_terms)
            
            return {
                "query_type": analysis.get("query_type", QueryType.GENERAL),
                "intent": analysis.get("intent", QueryIntent.INFORMATION),
                "problem_category": problem_category,
                "technical_terms": technical_terms,
                "urgency": urgency,
                "complexity": complexity,
                "keywords": analysis.get("keywords", []),
                "entities": analysis.get("entities", [])
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing problem: {e}")
            return {
                "query_type": QueryType.GENERAL,
                "intent": QueryIntent.INFORMATION,
                "problem_category": "general",
                "technical_terms": [],
                "urgency": "medium",
                "complexity": "medium",
                "keywords": query.split(),
                "entities": []
            }
    
    def _categorize_problem(self, query: str, analysis: Dict[str, Any]) -> str:
        """Categorize the problem based on content analysis"""
        
        query_lower = query.lower()
        
        # Define problem categories with keywords
        categories = {
            "authentication": ["auth", "login", "password", "token", "oauth", "sso", "authentication", "unauthorized", "401", "403"],
            "performance": ["slow", "performance", "timeout", "latency", "memory", "cpu", "optimization", "bottleneck"],
            "error_debugging": ["error", "exception", "bug", "crash", "failure", "debug", "stack trace", "500", "404"],
            "deployment": ["deploy", "deployment", "build", "ci/cd", "pipeline", "docker", "kubernetes", "infrastructure"],
            "database": ["database", "sql", "query", "connection", "migration", "schema", "db", "mysql", "postgres"],
            "api_integration": ["api", "rest", "graphql", "endpoint", "integration", "webhook", "microservice"],
            "configuration": ["config", "configuration", "settings", "environment", "properties", "yaml", "json"],
            "security": ["security", "vulnerability", "encryption", "ssl", "https", "certificate", "privacy"],
            "testing": ["test", "testing", "unit test", "integration test", "qa", "automation", "coverage"],
            "documentation": ["document", "documentation", "guide", "tutorial", "how to", "instructions"]
        }
        
        # Score each category
        category_scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                category_scores[category] = score
        
        # Return highest scoring category, default to "general"
        if category_scores:
            return max(category_scores, key=category_scores.get)
        else:
            return "general"
    
    def _extract_technical_terms(self, query: str) -> List[str]:
        """Extract technical terms from the query"""
        
        # Common technical terms patterns
        technical_patterns = [
            r'\b[A-Z][a-z]*(?:[A-Z][a-z]*)+\b',  # CamelCase
            r'\b[a-z]+(?:_[a-z]+)+\b',          # snake_case
            r'\b[a-z]+-[a-z]+(?:-[a-z]+)*\b',   # kebab-case
            r'\b\w+\.\w+(?:\.\w+)*\b',          # package.names
            r'\b[A-Z]{2,}\b',                   # Acronyms
            r'\b\d+\.\d+(?:\.\d+)*\b'          # Version numbers
        ]
        
        import re
        technical_terms = []
        for pattern in technical_patterns:
            matches = re.findall(pattern, query)
            technical_terms.extend(matches)
        
        return list(set(technical_terms))  # Remove duplicates
    
    def _assess_urgency(self, query: str) -> str:
        """Assess the urgency of the problem"""
        
        query_lower = query.lower()
        
        high_urgency = ["critical", "urgent", "emergency", "down", "production", "outage", "blocking", "broken"]
        medium_urgency = ["issue", "problem", "error", "bug", "failing"]
        
        if any(word in query_lower for word in high_urgency):
            return "high"
        elif any(word in query_lower for word in medium_urgency):
            return "medium"
        else:
            return "low"
    
    def _assess_complexity(self, query: str, technical_terms: List[str]) -> str:
        """Assess the complexity of the problem"""
        
        complexity_indicators = {
            "high": ["architecture", "scalability", "distributed", "microservices", "performance", "optimization"],
            "medium": ["integration", "configuration", "deployment", "testing", "debugging"],
            "low": ["how to", "tutorial", "example", "documentation"]
        }
        
        query_lower = query.lower()
        
        # Check complexity indicators
        for level, indicators in complexity_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                return level
        
        # Use technical terms count as fallback
        if len(technical_terms) > 3:
            return "high"
        elif len(technical_terms) > 1:
            return "medium"
        else:
            return "low"
    
    def _determine_search_strategy(self, problem_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Determine optimal search strategy based on problem analysis"""
        
        problem_category = problem_analysis["problem_category"]
        urgency = problem_analysis["urgency"]
        complexity = problem_analysis["complexity"]
        
        # Default strategy
        strategy = {
            "search_confluence": True,
            "search_jira": True,
            "search_code": True,
            "max_results": 10
        }
        
        # Adjust based on problem category
        category_strategies = {
            "documentation": {"search_confluence": True, "search_jira": False, "search_code": False, "max_results": 15},
            "error_debugging": {"search_jira": True, "search_code": True, "max_results": 20},
            "performance": {"search_code": True, "search_jira": True, "max_results": 15},
            "authentication": {"search_confluence": True, "search_code": True, "max_results": 12},
            "deployment": {"search_confluence": True, "search_jira": True, "max_results": 12},
            "api_integration": {"search_confluence": True, "search_code": True, "max_results": 15}
        }
        
        if problem_category in category_strategies:
            strategy.update(category_strategies[problem_category])
        
        # Adjust based on urgency
        if urgency == "high":
            strategy["max_results"] = min(strategy["max_results"] * 2, 30)
        
        # Adjust based on complexity
        if complexity == "high":
            strategy["search_confluence"] = True  # Always search docs for complex issues
            strategy["max_results"] = min(strategy["max_results"] + 5, 25)
        
        return strategy
    
    async def _collect_comprehensive_data(self, query: str, search_strategy: Dict[str, Any], problem_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Collect comprehensive data from all relevant sources with intelligent prioritization"""
        
        tasks = []
        task_sources = []
        
        # Build enhanced search queries
        enhanced_queries = self._build_enhanced_queries(query, problem_analysis)
        
        if search_strategy.get("search_confluence", True):
            tasks.append(self._search_confluence_enhanced(enhanced_queries, search_strategy.get("max_results", 10)))
            task_sources.append("confluence")
        
        if search_strategy.get("search_jira", True):
            tasks.append(self._search_jira_enhanced(enhanced_queries, search_strategy.get("max_results", 10), problem_analysis, search_strategy))
            task_sources.append("jira")
        
        if search_strategy.get("search_code", True):
            tasks.append(self._search_code_enhanced(enhanced_queries, search_strategy.get("file_types"), problem_analysis))
            task_sources.append("code")
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            processed_data = {"sources": {}}
            
            for i, result in enumerate(results):
                source = task_sources[i]
                if isinstance(result, Exception):
                    self.logger.error(f"Error searching {source}: {result}")
                    processed_data["sources"][source] = {"count": 0, "data": [], "error": str(result)}
                else:
                    # Enhance results with semantic analysis
                    enhanced_results = enhance_search_results(result, query)
                    processed_data["sources"][source] = {
                        "count": len(enhanced_results),
                        "data": enhanced_results,
                        "relevance_scores": [r.get("relevance_score", 0) for r in enhanced_results]
                    }
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error collecting data: {e}")
            return {"sources": {"confluence": {"count": 0, "data": []}, "jira": {"count": 0, "data": []}, "code": {"count": 0, "data": []}}}
    
    def _build_enhanced_queries(self, original_query: str, problem_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Build enhanced queries for different sources based on problem analysis"""
        
        technical_terms = problem_analysis.get("technical_terms", [])
        keywords = problem_analysis.get("keywords", [])
        problem_category = problem_analysis.get("problem_category", "general")
        
        # Base query
        base_query = original_query
        
        # Enhanced query with technical terms
        enhanced_query = base_query
        if technical_terms:
            enhanced_query += " " + " ".join(technical_terms)
        
        # Category-specific enhancements
        category_enhancements = {
            "authentication": "login oauth token auth security",
            "performance": "performance optimization slow latency",
            "error_debugging": "error exception debug troubleshooting",
            "deployment": "deployment build release configuration",
            "database": "database query sql connection migration",
            "api_integration": "api rest endpoint integration service"
        }
        
        if problem_category in category_enhancements:
            enhanced_query += " " + category_enhancements[problem_category]
        
        return {
            "original": original_query,
            "enhanced": enhanced_query,
            "technical": " ".join(technical_terms) if technical_terms else original_query,
            "keywords": " ".join(keywords) if keywords else original_query
        }
    
    async def _synthesize_solution(self, query: str, problem_analysis: Dict[str, Any], all_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize comprehensive solution from all collected data"""
        
        try:
            # Prepare context for AI analysis
            context_data = self._prepare_solution_context(query, problem_analysis, all_data)
            
            # Generate comprehensive solution using AI
            solution_prompt = self._build_solution_prompt(query, problem_analysis, context_data)
            
            solution_response = await self.ai_client.generate_response([
                {"role": "system", "content": "You are an expert software engineer and problem solver. Provide comprehensive, actionable solutions based on the context provided."},
                {"role": "user", "content": solution_prompt}
            ], max_tokens=2000)
            
            # Parse structured response
            solution_parts = self._parse_solution_response(solution_response)
            
            # Calculate confidence score
            confidence = self._calculate_confidence_score(all_data, problem_analysis)
            
            return {
                "solution": solution_parts.get("solution", solution_response),
                "steps": solution_parts.get("steps", []),
                "risks": solution_parts.get("risks", []),
                "related_issues": solution_parts.get("related_issues", []),
                "confidence": confidence
            }
            
        except Exception as e:
            self.logger.error(f"Error synthesizing solution: {e}")
            return {
                "solution": f"Error generating solution: {str(e)}",
                "steps": [],
                "risks": ["Solution generation failed"],
                "related_issues": [],
                "confidence": 0.0
            }
    
    def _prepare_solution_context(self, query: str, problem_analysis: Dict[str, Any], all_data: Dict[str, Any]) -> str:
        """Prepare comprehensive context for solution generation"""
        
        context_parts = [f"Problem Query: {query}"]
        context_parts.append(f"Problem Category: {problem_analysis.get('problem_category', 'general')}")
        context_parts.append(f"Urgency: {problem_analysis.get('urgency', 'medium')}")
        context_parts.append(f"Complexity: {problem_analysis.get('complexity', 'medium')}")
        
        sources = all_data.get("sources", {})
        
        # Add Confluence context
        confluence_data = sources.get("confluence", {}).get("data", [])
        if confluence_data:
            context_parts.append("\nRELEVANT DOCUMENTATION:")
            for doc in confluence_data[:3]:  # Top 3 most relevant
                context_parts.append(f"- {doc.get('title', 'N/A')}: {doc.get('excerpt', 'No excerpt')[:200]}...")
        
        # Add JIRA context
        jira_data = sources.get("jira", {}).get("data", [])
        if jira_data:
            context_parts.append("\nRELATED ISSUES:")
            for issue in jira_data[:3]:  # Top 3 most relevant
                context_parts.append(f"- {issue.get('key', 'N/A')}: {issue.get('summary', 'No summary')} (Status: {issue.get('status', 'N/A')})")
        
        # Add Code context
        code_data = sources.get("code", {}).get("data", [])
        if code_data:
            context_parts.append("\nRELEVANT CODE:")
            for code_file in code_data[:3]:  # Top 3 most relevant
                context_parts.append(f"- {code_file.get('file_path', 'N/A')}: {code_file.get('content_preview', 'No preview')[:150]}...")
        
        return "\n".join(context_parts)
    
    def _build_solution_prompt(self, query: str, problem_analysis: Dict[str, Any], context: str) -> str:
        """Build comprehensive prompt for solution generation"""
        
        return f"""Based on the following context, provide a comprehensive solution to the problem.

{context}

Please provide a structured response with:

1. SOLUTION SUMMARY: A clear, actionable solution to the problem

2. IMPLEMENTATION STEPS: Step-by-step instructions to implement the solution

3. POTENTIAL RISKS: Any risks or considerations to be aware of

4. RELATED ISSUES: Any related problems or considerations that might arise

Format your response clearly with these sections. Focus on practical, actionable advice that combines insights from the documentation, related issues, and code examples provided.
"""
    
    def _parse_solution_response(self, response: str) -> Dict[str, Any]:
        """Parse structured solution response"""
        
        # Simple parsing - look for section headers
        sections = {
            "solution": "",
            "steps": [],
            "risks": [],
            "related_issues": []
        }
        
        lines = response.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # Check for section headers
            if 'SOLUTION SUMMARY' in line.upper() or 'SOLUTION:' in line.upper():
                if current_section and current_content:
                    sections[current_section] = self._process_section_content(current_section, current_content)
                current_section = 'solution'
                current_content = []
            elif 'IMPLEMENTATION STEPS' in line.upper() or 'STEPS:' in line.upper():
                if current_section and current_content:
                    sections[current_section] = self._process_section_content(current_section, current_content)
                current_section = 'steps'
                current_content = []
            elif 'POTENTIAL RISKS' in line.upper() or 'RISKS:' in line.upper():
                if current_section and current_content:
                    sections[current_section] = self._process_section_content(current_section, current_content)
                current_section = 'risks'
                current_content = []
            elif 'RELATED ISSUES' in line.upper() or 'RELATED:' in line.upper():
                if current_section and current_content:
                    sections[current_section] = self._process_section_content(current_section, current_content)
                current_section = 'related_issues'
                current_content = []
            elif line and current_section:
                current_content.append(line)
        
        # Process final section
        if current_section and current_content:
            sections[current_section] = self._process_section_content(current_section, current_content)
        
        # If no sections were parsed, put everything in solution
        if not any(sections.values()) and response.strip():
            sections['solution'] = response.strip()
        
        return sections
    
    def _process_section_content(self, section: str, content: List[str]) -> Any:
        """Process content based on section type"""
        
        if section == 'solution':
            return '\n'.join(content).strip()
        else:  # steps, risks, related_issues
            items = []
            for line in content:
                if line.startswith(('- ', '* ', '1. ', '2. ', '3. ')):
                    items.append(line[2:].strip() if line.startswith(('- ', '* ')) else line.strip())
                elif line and not items:  # First non-list line
                    items.append(line.strip())
                elif line and items:  # Continue previous item
                    if items:
                        items[-1] += ' ' + line.strip()
            return items if items else ['\n'.join(content).strip()] if content else []
    
    def _calculate_confidence_score(self, all_data: Dict[str, Any], problem_analysis: Dict[str, Any]) -> float:
        """Calculate confidence score based on data quality and relevance"""
        
        sources = all_data.get("sources", {})
        
        # Base score
        confidence = 0.3
        
        # Add points for each source with data
        if sources.get("confluence", {}).get("count", 0) > 0:
            confluence_scores = sources["confluence"].get("relevance_scores", [0])
            confidence += 0.25 * (sum(confluence_scores) / len(confluence_scores) if confluence_scores else 0)
        
        if sources.get("jira", {}).get("count", 0) > 0:
            jira_scores = sources["jira"].get("relevance_scores", [0])
            confidence += 0.25 * (sum(jira_scores) / len(jira_scores) if jira_scores else 0)
        
        if sources.get("code", {}).get("count", 0) > 0:
            code_scores = sources["code"].get("relevance_scores", [0])
            confidence += 0.25 * (sum(code_scores) / len(code_scores) if code_scores else 0)
        
        # Adjust based on problem complexity
        if problem_analysis.get("complexity") == "low":
            confidence += 0.1
        elif problem_analysis.get("complexity") == "high":
            confidence -= 0.1
        
        return min(max(confidence, 0.0), 1.0)  # Clamp between 0 and 1
    
    async def _search_confluence_enhanced(self, queries: Dict[str, str], max_results: int) -> List[Dict[str, Any]]:
        """Enhanced Confluence search with multiple query strategies"""
        try:
            # Try different queries and combine results
            all_results = []
            
            # Search with enhanced query
            results1 = await self.confluence_client.search_pages(queries["enhanced"], max_results // 2)
            all_results.extend(results1)
            
            # Search with technical terms if different from enhanced
            if queries["technical"] != queries["enhanced"]:
                results2 = await self.confluence_client.search_pages(queries["technical"], max_results // 2)
                all_results.extend(results2)
            
            # Remove duplicates based on ID
            seen_ids = set()
            unique_results = []
            for result in all_results:
                result_id = result.get('id')
                if result_id and result_id not in seen_ids:
                    seen_ids.add(result_id)
                    unique_results.append(result)
            
            return unique_results[:max_results]
            
        except Exception as e:
            self.logger.error(f"Enhanced Confluence search failed: {e}")
            return []
    
    async def _search_jira_enhanced(self, queries: Dict[str, str], max_results: int, problem_analysis: Dict[str, Any], search_options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Enhanced JIRA search with problem-specific filters"""
        try:
            # Build filters based on problem analysis
            filters = {}
            
            if problem_analysis.get("urgency") == "high":
                filters["priority"] = ["High", "Critical", "Blocker"]
            
            problem_category = problem_analysis.get("problem_category")
            if problem_category in ["error_debugging", "performance"]:
                filters["status"] = ["Open", "In Progress", "Reopened"]
            
            # Add custom search filters if provided
            if search_options:
                if search_options.get("jira_key_prefixes"):
                    filters["issue_key_prefixes"] = search_options["jira_key_prefixes"]
            
            # Search with enhanced query and filters
            results = await self.jira_client.search_by_text(queries["enhanced"], max_results, **filters)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Enhanced JIRA search failed: {e}")
            return []
    
    async def _search_code_enhanced(self, queries: Dict[str, str], file_types: List[str], problem_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhanced code search with intelligent file type selection"""
        try:
            # Determine relevant file types based on problem analysis
            if not file_types:
                file_types = self._suggest_file_types(problem_analysis)
            
            # Search with multiple strategies
            all_results = []
            
            # Text search with enhanced query
            text_results = self.code_reader.search_files(queries["enhanced"], file_types)
            all_results.extend(text_results)
            
            # Search for technical terms in code
            for term in problem_analysis.get("technical_terms", []):
                if len(term) > 3:  # Avoid short terms
                    term_results = self.code_reader.search_files(term, file_types)
                    all_results.extend(term_results)
            
            # Remove duplicates and limit results
            seen_paths = set()
            unique_results = []
            for result in all_results:
                path = result.get('file_path')
                if path and path not in seen_paths:
                    seen_paths.add(path)
                    unique_results.append(result)
            
            return unique_results[:15]  # Limit code results
            
        except Exception as e:
            self.logger.error(f"Enhanced code search failed: {e}")
            return []
    
    def _suggest_file_types(self, problem_analysis: Dict[str, Any]) -> List[str]:
        """Suggest relevant file types based on problem analysis"""
        
        problem_category = problem_analysis.get("problem_category")
        
        category_file_types = {
            "authentication": [".java", ".py", ".js", ".ts", ".go"],
            "performance": [".java", ".py", ".js", ".go", ".cpp", ".c"],
            "database": [".sql", ".java", ".py", ".js", ".xml"],
            "deployment": [".yaml", ".yml", ".dockerfile", ".sh", ".json"],
            "configuration": [".properties", ".yaml", ".yml", ".json", ".xml", ".conf"],
            "api_integration": [".java", ".py", ".js", ".ts", ".json", ".yaml"],
            "testing": [".java", ".py", ".js", ".ts"]
        }
        
        return category_file_types.get(problem_category, [".java", ".py", ".js", ".json", ".yaml", ".sh"])
    
    def _build_user_context(self, search_strategy: Dict[str, Any], problem_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Build user context for ranking system"""
        
        user_context = {}
        
        try:
            # Extract team-relevant information from configuration
            if self.config:
                # JIRA projects as team context
                if hasattr(self.config, 'jira_projects') and self.config.jira_projects:
                    user_context['projects'] = self.config.jira_projects
                
                # JIRA issue key prefixes as team identifiers
                if hasattr(self.config, 'jira_issue_key_prefixes') and self.config.jira_issue_key_prefixes:
                    user_context['team_keywords'] = self.config.jira_issue_key_prefixes
                
                # Confluence spaces as team context
                if hasattr(self.config, 'confluence_spaces') and self.config.confluence_spaces:
                    user_context['spaces'] = self.config.confluence_spaces
            
            # Add problem-specific context
            user_context['problem_category'] = problem_analysis.get('problem_category', 'general')
            user_context['technical_terms'] = problem_analysis.get('technical_terms', [])
            user_context['urgency'] = problem_analysis.get('urgency', 'medium')
            user_context['complexity'] = problem_analysis.get('complexity', 'medium')
            
            # Add search strategy preferences
            user_context['search_preferences'] = search_strategy
            
            # Add timestamp for context freshness
            user_context['context_timestamp'] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"Error building user context: {e}")
            user_context = {'problem_category': 'general'}
        
        return user_context
    
    async def _search_confluence(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search Confluence for relevant documentation"""
        try:
            return await self.confluence_client.search_pages(query, max_results)
        except Exception as e:
            print(f"Confluence search failed: {str(e)}")
            return []
    
    async def _search_jira(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search JIRA for relevant issues"""
        try:
            return await self.jira_client.search_by_text(query, max_results)
        except Exception as e:
            print(f"JIRA search failed: {str(e)}")
            return []
    
    async def _search_code(self, query: str, file_types: List[str] = None) -> List[Dict[str, Any]]:
        """Search code repository for relevant files"""
        try:
            # Try both text search and pattern search
            text_results = self.code_reader.search_files(query, file_types)
            
            # If query looks like a pattern, also try pattern search
            pattern_results = []
            if any(char in query for char in ['*', '?', '[', ']', '^', '$']):
                pattern_results = self.code_reader.search_by_pattern(query, file_types)
            
            # Combine and deduplicate results
            all_results = text_results + pattern_results
            seen_paths = set()
            unique_results = []
            
            for result in all_results:
                if result['file_path'] not in seen_paths:
                    seen_paths.add(result['file_path'])
                    unique_results.append(result)
            
            return unique_results[:10]  # Limit to 10 results
            
        except Exception as e:
            print(f"Code search failed: {str(e)}")
            return []
    
    async def get_detailed_info(self, item_type: str, item_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific item"""
        
        if item_type == "confluence":
            return await self.confluence_client.get_page_content(item_id)
        elif item_type == "jira":
            return await self.jira_client.get_issue_details(item_id)
        elif item_type == "code":
            return self.code_reader.get_file_content(item_id)
        else:
            return {"error": f"Unknown item type: {item_type}"}
    
    async def suggest_related_queries(self, original_query: str, context: Dict[str, Any]) -> List[str]:
        """Suggest related queries based on the search results"""
        
        # Extract key terms from the context
        confluence_titles = [item.get('title', '') for item in context.get('sources', {}).get('confluence', {}).get('data', [])]
        jira_summaries = [item.get('summary', '') for item in context.get('sources', {}).get('jira', {}).get('data', [])]
        code_files = [item.get('file_path', '') for item in context.get('sources', {}).get('code', {}).get('data', [])]
        
        all_text = ' '.join(confluence_titles + jira_summaries + code_files)
        
        messages = [
            {
                "role": "system",
                "content": "Generate 3-5 related search queries based on the original query and context."
            },
            {
                "role": "user",
                "content": f"Original query: {original_query}\nContext: {all_text[:1000]}\n\nSuggest related queries:"
            }
        ]
        
        try:
            response = await self.ai_client.generate_response(messages, max_tokens=200)
            # Parse suggested queries from response
            queries = [line.strip('- ').strip() for line in response.split('\n') if line.strip().startswith('-')]
            return queries[:5]  # Limit to 5 suggestions
        except Exception as e:
            return [f"Error generating suggestions: {str(e)}"]
    
    async def close(self) -> None:
        """
        Close all connections and cleanup resources.
        
        Safe to call multiple times.
        """
        if not self._initialized:
            return
            
        self.logger.info("Closing AI Agent connections")
        
        try:
            # Close clients in reverse order of initialization
            if hasattr(self.jira_client, 'disconnect'):
                await self.jira_client.disconnect()
            
            if hasattr(self.confluence_client, 'disconnect'):
                await self.confluence_client.disconnect()
            
            if hasattr(self.ai_client, 'close'):
                await self.ai_client.close()
            
            self._initialized = False
            self.logger.info("AI Agent connections closed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            # Don't re-raise cleanup errors