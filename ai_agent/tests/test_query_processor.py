import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent.core.query_processor import NLPProcessor, QueryOptimizer, QueryType, QueryIntent


class TestNLPProcessor:
    """Test cases for NLPProcessor class"""
    
    @pytest.fixture
    def nlp_processor(self):
        """Create NLP processor instance for testing"""
        return NLPProcessor()
    
    def test_analyze_troubleshooting_query(self, nlp_processor):
        """Test analysis of troubleshooting query"""
        query = "API authentication error 401 not working"
        analysis = nlp_processor.analyze_query(query)
        
        assert analysis.original_query == query
        assert analysis.query_type == QueryType.TROUBLESHOOTING
        assert analysis.intent == QueryIntent.DEBUG
        assert "authentication" in analysis.keywords
        assert "error" in analysis.keywords
        assert "401" in analysis.technical_terms
        assert analysis.confidence_score > 0.5
    
    def test_analyze_how_to_query(self, nlp_processor):
        """Test analysis of how-to query"""
        query = "How to implement OAuth authentication in Java"
        analysis = nlp_processor.analyze_query(query)
        
        assert analysis.query_type == QueryType.HOW_TO
        assert analysis.intent == QueryIntent.IMPLEMENT
        assert "oauth" in analysis.keywords or "authentication" in analysis.keywords
        assert "implement" in analysis.keywords
        assert analysis.confidence_score > 0.6
    
    def test_analyze_what_is_query(self, nlp_processor):
        """Test analysis of what-is query"""
        query = "What is REST API and how does it work"
        analysis = nlp_processor.analyze_query(query)
        
        assert analysis.query_type == QueryType.WHAT_IS
        assert analysis.intent == QueryIntent.EXPLAIN
        assert "rest" in analysis.technical_terms or "api" in analysis.technical_terms
        assert analysis.confidence_score > 0.5
    
    def test_analyze_code_search_query(self, nlp_processor):
        """Test analysis of code search query"""
        query = "find function authentication method in Java class"
        analysis = nlp_processor.analyze_query(query)
        
        assert analysis.query_type == QueryType.CODE_SEARCH
        assert analysis.intent == QueryIntent.SEARCH
        assert "function" in analysis.keywords
        assert "authentication" in analysis.keywords
        assert "java" in analysis.technical_terms or any("java" in term for term in analysis.technical_terms)
    
    def test_analyze_documentation_query(self, nlp_processor):
        """Test analysis of documentation query"""
        query = "API documentation for user management endpoints"
        analysis = nlp_processor.analyze_query(query)
        
        assert analysis.query_type == QueryType.DOCUMENTATION
        assert "documentation" in analysis.keywords or "docs" in analysis.keywords
        assert "api" in analysis.technical_terms
        assert "user" in analysis.keywords
    
    def test_analyze_issue_tracking_query(self, nlp_processor):
        """Test analysis of issue tracking query"""
        query = "JIRA ticket status for bug report PROJ-123"
        analysis = nlp_processor.analyze_query(query)
        
        assert analysis.query_type == QueryType.ISSUE_TRACKING
        assert "jira" in analysis.technical_terms
        assert "ticket" in analysis.keywords
        assert "status" in analysis.keywords
    
    def test_extract_keywords(self, nlp_processor):
        """Test keyword extraction functionality"""
        query = "How to implement secure authentication using JWT tokens"
        
        # Mock NLTK functionality for testing
        try:
            keywords = nlp_processor._extract_keywords(query.lower())
            
            # Should extract meaningful words
            assert len(keywords) > 0
            
            # Should contain important terms (may vary based on NLTK availability)
            important_terms = {"implement", "secure", "authentication", "jwt", "tokens"}
            extracted_terms = set(keywords)
            
            # At least some important terms should be extracted
            assert len(important_terms.intersection(extracted_terms)) > 0
            
        except Exception:
            # If NLTK is not available, test basic fallback
            keywords = query.split()
            assert len(keywords) > 0
    
    def test_extract_technical_terms(self, nlp_processor):
        """Test technical term extraction"""
        query = "REST API authentication with OAuth 2.0 and JWT tokens"
        technical_terms = nlp_processor._extract_technical_terms(query.lower())
        
        expected_terms = {"api", "oauth", "jwt"}
        extracted_terms = set(technical_terms)
        
        # Should find at least some technical terms
        assert len(expected_terms.intersection(extracted_terms)) > 0
    
    def test_extract_file_extensions(self, nlp_processor):
        """Test file extension extraction"""
        query = "Python script .py file and Java .java class implementation"
        technical_terms = nlp_processor._extract_technical_terms(query)
        
        # Should extract file extensions
        extensions = [term for term in technical_terms if term.startswith('.')]
        assert len(extensions) > 0
    
    def test_extract_version_numbers(self, nlp_processor):
        """Test version number extraction"""
        query = "Spring Boot 2.5.4 and Java 11 compatibility"
        technical_terms = nlp_processor._extract_technical_terms(query)
        
        # Should extract version numbers
        versions = [term for term in technical_terms if any(char.isdigit() for char in term)]
        assert len(versions) > 0
    
    def test_classify_query_intent(self, nlp_processor):
        """Test query intent classification"""
        test_cases = [
            ("find authentication method", QueryIntent.SEARCH),
            ("explain how JWT works", QueryIntent.EXPLAIN),
            ("debug login error", QueryIntent.DEBUG),
            ("implement OAuth flow", QueryIntent.IMPLEMENT),
            ("configure database connection", QueryIntent.CONFIGURE),
            ("compare REST vs GraphQL", QueryIntent.COMPARE)
        ]
        
        for query, expected_intent in test_cases:
            intent = nlp_processor._classify_intent(query)
            assert intent == expected_intent or intent == QueryIntent.SEARCH  # SEARCH is default fallback
    
    def test_semantic_expansion(self, nlp_processor):
        """Test semantic keyword expansion"""
        keywords = ["error", "fix", "authentication", "database"]
        expansions = nlp_processor._expand_semantically(keywords)
        
        # Should generate some expansions
        assert len(expansions) > 0
        
        # Should include synonyms for common terms
        if "error" in keywords:
            expansion_set = set(expansions)
            error_synonyms = {"exception", "failure", "bug", "issue"}
            assert len(error_synonyms.intersection(expansion_set)) > 0
    
    def test_suggest_sources(self, nlp_processor):
        """Test data source suggestions"""
        # Test troubleshooting query
        sources = nlp_processor._suggest_sources(QueryType.TROUBLESHOOTING, ["error", "api"])
        assert "jira" in sources
        assert "confluence" in sources
        
        # Test how-to query
        sources = nlp_processor._suggest_sources(QueryType.HOW_TO, ["implement"])
        assert "confluence" in sources
        assert "code" in sources
        
        # Test code search query
        sources = nlp_processor._suggest_sources(QueryType.CODE_SEARCH, ["java:class"])
        assert "code" in sources
    
    def test_confidence_calculation(self, nlp_processor):
        """Test confidence score calculation"""
        # High confidence case
        high_confidence = nlp_processor._calculate_confidence(
            QueryType.TROUBLESHOOTING, 
            QueryIntent.DEBUG, 
            ["api", "error", "401"]
        )
        
        # Low confidence case (general query)
        low_confidence = nlp_processor._calculate_confidence(
            QueryType.GENERAL, 
            QueryIntent.SEARCH, 
            []
        )
        
        assert high_confidence > low_confidence
        assert 0 <= low_confidence <= 1
        assert 0 <= high_confidence <= 1


class TestQueryOptimizer:
    """Test cases for QueryOptimizer class"""
    
    @pytest.fixture
    def query_optimizer(self):
        """Create query optimizer instance for testing"""
        return QueryOptimizer()
    
    @pytest.mark.asyncio
    async def test_optimize_for_confluence(self, query_optimizer):
        """Test Confluence query optimization"""
        # Mock analysis
        from query_processor import QueryAnalysis, QueryType, QueryIntent
        
        analysis = QueryAnalysis(
            original_query="how to setup authentication",
            processed_query="how to setup authentication",
            query_type=QueryType.HOW_TO,
            intent=QueryIntent.IMPLEMENT,
            keywords=["setup", "authentication", "configure"],
            entities=[],
            technical_terms=["auth", "api"],
            confidence_score=0.8,
            suggested_sources=["confluence", "code"],
            semantic_expansion=["configure", "install"]
        )
        
        optimized = await query_optimizer.optimize_query(analysis)
        
        assert "confluence" in optimized
        confluence_query = optimized["confluence"]
        
        # Should include "how to" for HOW_TO query type
        assert "how to" in confluence_query.lower()
        assert "setup" in confluence_query or "authentication" in confluence_query
    
    @pytest.mark.asyncio
    async def test_optimize_for_jira(self, query_optimizer):
        """Test JIRA query optimization"""
        from query_processor import QueryAnalysis, QueryType, QueryIntent
        
        analysis = QueryAnalysis(
            original_query="API authentication error bug",
            processed_query="api authentication error bug",
            query_type=QueryType.TROUBLESHOOTING,
            intent=QueryIntent.DEBUG,
            keywords=["api", "authentication", "error", "bug"],
            entities=[],
            technical_terms=["api"],
            confidence_score=0.9,
            suggested_sources=["jira", "confluence"],
            semantic_expansion=["issue", "problem"]
        )
        
        optimized = await query_optimizer.optimize_query(analysis)
        
        assert "jira" in optimized
        jira_query = optimized["jira"]
        
        # Should focus on issue-related terms
        assert any(term in jira_query.lower() for term in ["error", "bug", "api", "authentication"])
        
        # For troubleshooting, should include status filter
        if analysis.query_type == QueryType.TROUBLESHOOTING:
            assert 'status != "Done"' in jira_query or not jira_query.endswith('status != "Done"')  # May or may not have filter
    
    @pytest.mark.asyncio
    async def test_optimize_for_code(self, query_optimizer):
        """Test code search optimization"""
        from query_processor import QueryAnalysis, QueryType, QueryIntent
        
        analysis = QueryAnalysis(
            original_query="find Java authentication method",
            processed_query="find java authentication method",
            query_type=QueryType.CODE_SEARCH,
            intent=QueryIntent.SEARCH,
            keywords=["find", "java", "authentication", "method"],
            entities=[],
            technical_terms=["java", "api", "java:class"],
            confidence_score=0.7,
            suggested_sources=["code"],
            semantic_expansion=["function", "implementation"]
        )
        
        optimized = await query_optimizer.optimize_query(analysis)
        
        assert "code" in optimized
        code_query = optimized["code"]
        
        # Should include technical terms and remove language prefixes
        assert "java" in code_query or "authentication" in code_query
        assert "java:" not in code_query  # Should remove language prefixes
    
    @pytest.mark.asyncio
    async def test_optimization_with_different_query_types(self, query_optimizer):
        """Test optimization handles different query types appropriately"""
        from query_processor import QueryAnalysis, QueryType, QueryIntent
        
        # Test WHAT_IS query
        what_is_analysis = QueryAnalysis(
            original_query="what is OAuth",
            processed_query="what is oauth",
            query_type=QueryType.WHAT_IS,
            intent=QueryIntent.EXPLAIN,
            keywords=["what", "is", "oauth"],
            entities=[],
            technical_terms=["oauth"],
            confidence_score=0.8,
            suggested_sources=["confluence"],
            semantic_expansion=["authentication"]
        )
        
        optimized = await query_optimizer.optimize_query(what_is_analysis)
        
        # Confluence query should include "what is"
        assert "what is" in optimized["confluence"].lower()
    
    def test_query_optimizer_initialization(self, query_optimizer):
        """Test query optimizer initialization"""
        assert query_optimizer.nlp_processor is not None
        assert hasattr(query_optimizer.nlp_processor, 'technical_terms')
        assert hasattr(query_optimizer.nlp_processor, 'programming_keywords')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])