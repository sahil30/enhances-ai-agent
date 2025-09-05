import asyncio
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import structlog

logger = structlog.get_logger(__name__)


class QueryType(Enum):
    """Types of queries the system can handle"""
    TROUBLESHOOTING = "troubleshooting"
    HOW_TO = "how_to"
    WHAT_IS = "what_is"
    CODE_SEARCH = "code_search"
    DOCUMENTATION = "documentation"
    ISSUE_TRACKING = "issue_tracking"
    GENERAL = "general"


class QueryIntent(Enum):
    """User intent classification"""
    SEARCH = "search"
    EXPLAIN = "explain"
    DEBUG = "debug"
    IMPLEMENT = "implement"
    CONFIGURE = "configure"
    COMPARE = "compare"


@dataclass
class QueryAnalysis:
    """Result of query analysis"""
    original_query: str
    processed_query: str
    query_type: QueryType
    intent: QueryIntent
    keywords: List[str]
    entities: List[str]
    technical_terms: List[str]
    confidence_score: float
    suggested_sources: List[str]
    semantic_expansion: List[str]


class NLPProcessor:
    """Natural Language Processing for query analysis"""
    
    def __init__(self):
        self.stemmer = PorterStemmer()
        self.lemmatizer = WordNetLemmatizer()
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 3)
        )
        
        # Technical vocabulary
        self.technical_terms = self._load_technical_terms()
        self.programming_keywords = self._load_programming_keywords()
        
        # Pattern matching for query types
        self.query_patterns = {
            QueryType.TROUBLESHOOTING: [
                r'\b(error|exception|bug|issue|problem|fail|broken|not working)\b',
                r'\b(fix|solve|resolve|debug)\b',
                r'\b(timeout|crash|hang)\b'
            ],
            QueryType.HOW_TO: [
                r'\bhow\s+(to|do|can)\b',
                r'\bsteps?\s+to\b',
                r'\bguide\s+for\b',
                r'\bimplement\b'
            ],
            QueryType.WHAT_IS: [
                r'\bwhat\s+(is|are)\b',
                r'\bdefine\b',
                r'\bexplain\b',
                r'\btell\s+me\s+about\b'
            ],
            QueryType.CODE_SEARCH: [
                r'\b(function|method|class|variable)\b',
                r'\b(code|implementation|source)\b',
                r'\b(find|search|locate)\b.*\b(code|file)\b'
            ],
            QueryType.DOCUMENTATION: [
                r'\bdocumentation\b',
                r'\bdocs?\b',
                r'\bmanual\b',
                r'\bspecification\b'
            ],
            QueryType.ISSUE_TRACKING: [
                r'\b(ticket|issue|bug\s+report)\b',
                r'\b(jira|track)\b',
                r'\b(status|progress)\b'
            ]
        }
        
        self.intent_patterns = {
            QueryIntent.SEARCH: [
                r'\b(find|search|locate|look\s+for)\b',
                r'\bwhere\s+(is|can)\b'
            ],
            QueryIntent.EXPLAIN: [
                r'\b(explain|describe|tell|what)\b',
                r'\bhow\s+does\b',
                r'\bwhy\s+does\b'
            ],
            QueryIntent.DEBUG: [
                r'\b(debug|troubleshoot|fix|solve)\b',
                r'\berror\b',
                r'\bnot\s+working\b'
            ],
            QueryIntent.IMPLEMENT: [
                r'\b(implement|create|build|develop)\b',
                r'\bhow\s+to\s+(make|create|build)\b'
            ],
            QueryIntent.CONFIGURE: [
                r'\b(configure|setup|install|config)\b',
                r'\bsettings?\b'
            ],
            QueryIntent.COMPARE: [
                r'\b(compare|vs|versus|difference)\b',
                r'\bwhich\s+(is\s+)?better\b'
            ]
        }
    
    def _load_technical_terms(self) -> List[str]:
        """Load technical terms dictionary"""
        return [
            'api', 'rest', 'http', 'https', 'json', 'xml', 'database', 'sql',
            'authentication', 'authorization', 'oauth', 'jwt', 'token', 'session',
            'microservice', 'container', 'docker', 'kubernetes', 'deployment',
            'pipeline', 'ci', 'cd', 'git', 'branch', 'merge', 'commit',
            'framework', 'library', 'dependency', 'package', 'module',
            'cache', 'redis', 'mongodb', 'postgresql', 'mysql',
            'server', 'client', 'frontend', 'backend', 'fullstack',
            'test', 'unit', 'integration', 'e2e', 'mock', 'stub'
        ]
    
    def _load_programming_keywords(self) -> Dict[str, List[str]]:
        """Load programming language keywords"""
        return {
            'java': ['class', 'interface', 'extends', 'implements', 'public', 'private', 'static'],
            'python': ['def', 'class', 'import', 'from', 'if', 'else', 'try', 'except'],
            'javascript': ['function', 'var', 'let', 'const', 'async', 'await', 'promise'],
            'shell': ['#!/bin/bash', 'if', 'then', 'else', 'fi', 'for', 'while', 'do', 'done']
        }
    
    def analyze_query(self, query: str) -> QueryAnalysis:
        """Comprehensive query analysis"""
        logger.info(f"Analyzing query: {query}")
        
        # Basic preprocessing
        processed_query = self._preprocess_query(query)
        
        # Extract components
        keywords = self._extract_keywords(processed_query)
        entities = self._extract_entities(query)
        technical_terms = self._extract_technical_terms(processed_query)
        
        # Classification
        query_type = self._classify_query_type(query)
        intent = self._classify_intent(query)
        
        # Semantic expansion
        semantic_expansion = self._expand_semantically(keywords)
        
        # Source suggestions
        suggested_sources = self._suggest_sources(query_type, technical_terms)
        
        # Confidence scoring
        confidence_score = self._calculate_confidence(query_type, intent, technical_terms)
        
        analysis = QueryAnalysis(
            original_query=query,
            processed_query=processed_query,
            query_type=query_type,
            intent=intent,
            keywords=keywords,
            entities=entities,
            technical_terms=technical_terms,
            confidence_score=confidence_score,
            suggested_sources=suggested_sources,
            semantic_expansion=semantic_expansion
        )
        
        logger.info(f"Query analysis complete", 
                   query_type=query_type.value, 
                   intent=intent.value, 
                   confidence=confidence_score)
        
        return analysis
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess query text"""
        # Convert to lowercase
        processed = query.lower()
        
        # Remove special characters but keep important ones
        processed = re.sub(r'[^\w\s\-\.]', ' ', processed)
        
        # Remove extra whitespace
        processed = re.sub(r'\s+', ' ', processed).strip()
        
        return processed
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords using NLP"""
        try:
            # Download required NLTK data if not present
            try:
                nltk.data.find('tokenizers/punkt')
                nltk.data.find('corpora/stopwords')
                nltk.data.find('taggers/averaged_perceptron_tagger')
            except LookupError:
                logger.warning("NLTK data not found, using basic keyword extraction")
                return query.split()
            
            # Tokenize and remove stopwords
            tokens = word_tokenize(query)
            stop_words = set(stopwords.words('english'))
            
            # POS tagging to keep only meaningful words
            pos_tags = pos_tag(tokens)
            keywords = []
            
            for word, pos in pos_tags:
                if (word.lower() not in stop_words and 
                    len(word) > 2 and 
                    pos in ['NN', 'NNS', 'NNP', 'NNPS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'JJ']):
                    keywords.append(word.lower())
            
            # Add stemmed versions
            stemmed_keywords = [self.stemmer.stem(word) for word in keywords]
            
            return list(set(keywords + stemmed_keywords))
        
        except Exception as e:
            logger.warning(f"Error in keyword extraction: {e}")
            return query.split()
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract named entities from query"""
        try:
            tokens = word_tokenize(query)
            pos_tags = pos_tag(tokens)
            chunks = ne_chunk(pos_tags)
            
            entities = []
            for chunk in chunks:
                if hasattr(chunk, 'label'):
                    entity = ' '.join([token for token, pos in chunk.leaves()])
                    entities.append(entity)
            
            return entities
        
        except Exception as e:
            logger.warning(f"Error in entity extraction: {e}")
            return []
    
    def _extract_technical_terms(self, query: str) -> List[str]:
        """Extract technical terms from query"""
        found_terms = []
        query_words = query.split()
        
        # Check for technical terms
        for term in self.technical_terms:
            if term in query:
                found_terms.append(term)
        
        # Check for programming language keywords
        for lang, keywords in self.programming_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    found_terms.append(f"{lang}:{keyword}")
        
        # Extract file extensions
        file_extensions = re.findall(r'\.\w{2,4}\b', query)
        found_terms.extend(file_extensions)
        
        # Extract version numbers
        versions = re.findall(r'v?\d+\.\d+(?:\.\d+)?', query)
        found_terms.extend(versions)
        
        return list(set(found_terms))
    
    def _classify_query_type(self, query: str) -> QueryType:
        """Classify query type using pattern matching"""
        query_lower = query.lower()
        type_scores = {}
        
        for query_type, patterns in self.query_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, query_lower)
                score += len(matches)
            type_scores[query_type] = score
        
        # Return type with highest score, or GENERAL if no matches
        if type_scores and max(type_scores.values()) > 0:
            return max(type_scores, key=type_scores.get)
        return QueryType.GENERAL
    
    def _classify_intent(self, query: str) -> QueryIntent:
        """Classify user intent"""
        query_lower = query.lower()
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, query_lower)
                score += len(matches)
            intent_scores[intent] = score
        
        # Return intent with highest score, or SEARCH as default
        if intent_scores and max(intent_scores.values()) > 0:
            return max(intent_scores, key=intent_scores.get)
        return QueryIntent.SEARCH
    
    def _expand_semantically(self, keywords: List[str]) -> List[str]:
        """Expand keywords with semantic alternatives"""
        expansions = []
        
        # Synonym mapping for common technical terms
        synonyms = {
            'error': ['exception', 'failure', 'bug', 'issue'],
            'fix': ['resolve', 'solve', 'repair', 'correct'],
            'setup': ['configure', 'install', 'initialize'],
            'api': ['endpoint', 'service', 'interface'],
            'database': ['db', 'datastore', 'repository'],
            'authentication': ['auth', 'login', 'credentials'],
            'configuration': ['config', 'settings', 'parameters']
        }
        
        for keyword in keywords:
            if keyword in synonyms:
                expansions.extend(synonyms[keyword])
        
        return list(set(expansions))
    
    def _suggest_sources(self, query_type: QueryType, technical_terms: List[str]) -> List[str]:
        """Suggest relevant data sources based on query analysis"""
        sources = []
        
        # Default sources for all queries
        if query_type in [QueryType.TROUBLESHOOTING, QueryType.ISSUE_TRACKING]:
            sources.extend(['jira', 'confluence'])
        elif query_type in [QueryType.HOW_TO, QueryType.DOCUMENTATION]:
            sources.extend(['confluence', 'code'])
        elif query_type == QueryType.CODE_SEARCH:
            sources.extend(['code', 'confluence'])
        else:
            sources = ['confluence', 'jira', 'code']
        
        # Prioritize based on technical terms
        code_indicators = [term for term in technical_terms if any(
            lang_keyword in term for lang_keyword in ['java:', 'python:', 'javascript:', 'shell:']
        )]
        if code_indicators:
            sources.insert(0, 'code')
        
        return list(set(sources))
    
    def _calculate_confidence(self, query_type: QueryType, intent: QueryIntent, 
                            technical_terms: List[str]) -> float:
        """Calculate confidence score for the analysis"""
        base_confidence = 0.5
        
        # Boost confidence for clear patterns
        if query_type != QueryType.GENERAL:
            base_confidence += 0.2
        
        if intent != QueryIntent.SEARCH:
            base_confidence += 0.1
        
        # Technical terms indicate domain expertise
        if technical_terms:
            base_confidence += min(0.2, len(technical_terms) * 0.05)
        
        return min(1.0, base_confidence)


class QueryOptimizer:
    """Optimize queries for better search results"""
    
    def __init__(self):
        self.nlp_processor = NLPProcessor()
    
    async def optimize_query(self, analysis: QueryAnalysis) -> Dict[str, str]:
        """Generate optimized queries for different sources"""
        optimized_queries = {}
        
        # Base optimization
        base_terms = analysis.keywords + analysis.technical_terms + analysis.semantic_expansion
        
        # Confluence optimization (documentation focused)
        confluence_query = self._optimize_for_confluence(analysis, base_terms)
        optimized_queries['confluence'] = confluence_query
        
        # JIRA optimization (issue tracking focused)
        jira_query = self._optimize_for_jira(analysis, base_terms)
        optimized_queries['jira'] = jira_query
        
        # Code optimization (code search focused)
        code_query = self._optimize_for_code(analysis, base_terms)
        optimized_queries['code'] = code_query
        
        logger.debug("Query optimization complete", optimized_queries=optimized_queries)
        return optimized_queries
    
    def _optimize_for_confluence(self, analysis: QueryAnalysis, terms: List[str]) -> str:
        """Optimize query for Confluence search"""
        # Prioritize documentation-related terms
        priority_terms = []
        regular_terms = []
        
        for term in terms:
            if any(keyword in term.lower() for keyword in ['doc', 'guide', 'manual', 'how', 'setup']):
                priority_terms.append(term)
            else:
                regular_terms.append(term)
        
        # Build query with priority terms first
        all_terms = priority_terms + regular_terms[:10]  # Limit to prevent overly long queries
        
        if analysis.query_type == QueryType.HOW_TO:
            return f"how to {' '.join(all_terms)}"
        elif analysis.query_type == QueryType.WHAT_IS:
            return f"what is {' '.join(all_terms)}"
        else:
            return ' '.join(all_terms)
    
    def _optimize_for_jira(self, analysis: QueryAnalysis, terms: List[str]) -> str:
        """Optimize query for JIRA search"""
        # Focus on issue-related terms
        issue_terms = []
        other_terms = []
        
        for term in terms:
            if any(keyword in term.lower() for keyword in ['error', 'bug', 'issue', 'fail', 'problem']):
                issue_terms.append(term)
            else:
                other_terms.append(term)
        
        # Combine terms for JIRA JQL
        all_terms = issue_terms + other_terms[:8]  # JIRA queries should be more focused
        query_text = ' '.join(all_terms)
        
        # Add status filtering for active issues if troubleshooting
        if analysis.query_type == QueryType.TROUBLESHOOTING:
            return f'{query_text} AND status != "Done"'
        
        return query_text
    
    def _optimize_for_code(self, analysis: QueryAnalysis, terms: List[str]) -> str:
        """Optimize query for code search"""
        # Focus on technical and programming terms
        code_terms = []
        
        for term in terms:
            # Include programming language keywords and technical terms
            if (any(lang in term for lang in ['java:', 'python:', 'javascript:', 'shell:']) or
                term in self.nlp_processor.technical_terms or
                re.match(r'\.(java|py|js|sh|json)$', term)):
                code_terms.append(term.replace(':', ' '))
            else:
                code_terms.append(term)
        
        # Limit to most relevant terms
        return ' '.join(code_terms[:12])


# Global processor instance
query_processor = NLPProcessor()
query_optimizer = QueryOptimizer()