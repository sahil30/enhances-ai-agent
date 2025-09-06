"""
Advanced Result Ranking System

Implements sophisticated relevance scoring for search results across
Confluence, JIRA, and code repositories with multiple ranking factors:
- Content relevance and keyword matching
- Recency weighting (newer content ranked higher)
- Cross-source correlation (related items boost each other)
- Team-specific relevance (user/team context)
- Historical interaction data
- Content quality indicators
"""

import re
import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import structlog

logger = structlog.get_logger(__name__)


class AdvancedRankingEngine:
    """Advanced ranking engine for multi-source search results"""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = structlog.get_logger("ranking_engine")
        
        # Ranking weights (can be tuned based on usage data)
        self.weights = {
            'content_relevance': 0.35,      # How well content matches query
            'recency': 0.20,                # How recent the content is
            'cross_source_correlation': 0.15, # Correlation across sources
            'team_relevance': 0.15,         # Team/user context relevance
            'quality_indicators': 0.10,     # Content quality signals
            'interaction_history': 0.05     # Historical user interactions
        }
        
        # Cache for performance
        self.correlation_cache = {}
        self.team_context_cache = {}
    
    def rank_all_results(self, all_results: Dict[str, Any], query: str, 
                        user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Rank all search results across sources with advanced scoring
        
        Args:
            all_results: Dictionary containing results from all sources
            query: Original search query
            user_context: User/team context information
        
        Returns:
            Enhanced results with ranking scores and cross-correlations
        """
        try:
            self.logger.info(f"Starting advanced ranking for query: {query}")
            
            if not user_context:
                user_context = {}
            
            # Extract and prepare data
            confluence_results = all_results.get("sources", {}).get("confluence", {}).get("data", [])
            jira_results = all_results.get("sources", {}).get("jira", {}).get("data", [])
            code_results = all_results.get("sources", {}).get("code", {}).get("data", [])
            
            # Calculate advanced scores for each source
            ranked_confluence = self._rank_confluence_results(confluence_results, query, user_context)
            ranked_jira = self._rank_jira_results(jira_results, query, user_context)
            ranked_code = self._rank_code_results(code_results, query, user_context)
            
            # Calculate cross-source correlations
            cross_correlations = self._calculate_cross_source_correlations(
                ranked_confluence, ranked_jira, ranked_code, query
            )
            
            # Apply cross-correlation boosts
            self._apply_correlation_boosts(ranked_confluence, ranked_jira, ranked_code, cross_correlations)
            
            # Generate unified ranking insights
            ranking_insights = self._generate_ranking_insights(
                ranked_confluence, ranked_jira, ranked_code, cross_correlations, query
            )
            
            # Update original results with enhanced ranking
            enhanced_results = all_results.copy()
            enhanced_results["sources"]["confluence"]["data"] = ranked_confluence
            enhanced_results["sources"]["jira"]["data"] = ranked_jira
            enhanced_results["sources"]["code"]["data"] = ranked_code
            enhanced_results["ranking_insights"] = ranking_insights
            enhanced_results["cross_correlations"] = cross_correlations
            
            self.logger.info(f"Advanced ranking completed for {len(confluence_results + jira_results + code_results)} results")
            
            return enhanced_results
            
        except Exception as e:
            self.logger.error(f"Error in advanced ranking: {e}")
            return all_results  # Return original results if ranking fails
    
    def _rank_confluence_results(self, results: List[Dict], query: str, user_context: Dict) -> List[Dict]:
        """Rank Confluence results with advanced scoring"""
        
        for result in results:
            try:
                scores = {}
                
                # Content relevance (0.35 weight)
                scores['content_relevance'] = self._calculate_content_relevance(
                    result, query, 'confluence'
                )
                
                # Recency scoring (0.20 weight)  
                scores['recency'] = self._calculate_recency_score(
                    result.get('last_modified'), result.get('created')
                )
                
                # Team relevance (0.15 weight)
                scores['team_relevance'] = self._calculate_team_relevance(
                    result, user_context, 'confluence'
                )
                
                # Quality indicators (0.10 weight)
                scores['quality_indicators'] = self._calculate_confluence_quality_score(result)
                
                # Calculate composite score
                composite_score = sum(
                    scores[factor] * self.weights[factor] 
                    for factor in scores
                )
                
                # Add ranking metadata
                result['ranking_score'] = composite_score
                result['ranking_breakdown'] = scores
                result['ranking_factors'] = self._explain_ranking_factors(scores, 'confluence')
                
            except Exception as e:
                self.logger.warning(f"Error ranking Confluence result: {e}")
                result['ranking_score'] = 0.5  # Default fallback score
        
        # Sort by ranking score
        return sorted(results, key=lambda x: x.get('ranking_score', 0), reverse=True)
    
    def _rank_jira_results(self, results: List[Dict], query: str, user_context: Dict) -> List[Dict]:
        """Rank JIRA results with advanced scoring"""
        
        for result in results:
            try:
                scores = {}
                
                # Content relevance (0.35 weight)
                scores['content_relevance'] = self._calculate_content_relevance(
                    result, query, 'jira'
                )
                
                # Recency scoring (0.20 weight)
                scores['recency'] = self._calculate_recency_score(
                    result.get('updated'), result.get('created')
                )
                
                # Team relevance (0.15 weight)
                scores['team_relevance'] = self._calculate_team_relevance(
                    result, user_context, 'jira'
                )
                
                # Quality indicators (0.10 weight)
                scores['quality_indicators'] = self._calculate_jira_quality_score(result)
                
                # JIRA-specific factors
                scores['priority_boost'] = self._calculate_priority_boost(result)
                scores['status_relevance'] = self._calculate_status_relevance(result, query)
                
                # Calculate composite score
                composite_score = sum(
                    scores[factor] * self.weights.get(factor, 0.05) 
                    for factor in scores
                )
                
                result['ranking_score'] = composite_score
                result['ranking_breakdown'] = scores
                result['ranking_factors'] = self._explain_ranking_factors(scores, 'jira')
                
            except Exception as e:
                self.logger.warning(f"Error ranking JIRA result: {e}")
                result['ranking_score'] = 0.5
        
        return sorted(results, key=lambda x: x.get('ranking_score', 0), reverse=True)
    
    def _rank_code_results(self, results: List[Dict], query: str, user_context: Dict) -> List[Dict]:
        """Rank code results with advanced scoring"""
        
        for result in results:
            try:
                scores = {}
                
                # Content relevance (0.35 weight)
                scores['content_relevance'] = self._calculate_content_relevance(
                    result, query, 'code'
                )
                
                # Recency scoring (0.20 weight)
                scores['recency'] = self._calculate_file_recency_score(result)
                
                # Team relevance (0.15 weight)
                scores['team_relevance'] = self._calculate_team_relevance(
                    result, user_context, 'code'
                )
                
                # Quality indicators (0.10 weight)
                scores['quality_indicators'] = self._calculate_code_quality_score(result)
                
                # Code-specific factors
                scores['match_density'] = self._calculate_match_density(result, query)
                scores['file_importance'] = self._calculate_file_importance(result)
                
                # Calculate composite score
                composite_score = sum(
                    scores[factor] * self.weights.get(factor, 0.05) 
                    for factor in scores
                )
                
                result['ranking_score'] = composite_score
                result['ranking_breakdown'] = scores
                result['ranking_factors'] = self._explain_ranking_factors(scores, 'code')
                
            except Exception as e:
                self.logger.warning(f"Error ranking code result: {e}")
                result['ranking_score'] = 0.5
        
        return sorted(results, key=lambda x: x.get('ranking_score', 0), reverse=True)
    
    def _calculate_content_relevance(self, result: Dict, query: str, source_type: str) -> float:
        """Calculate content relevance score based on query matching"""
        
        query_terms = set(query.lower().split())
        if not query_terms:
            return 0.5
        
        # Extract text content based on source type
        if source_type == 'confluence':
            text_content = f"{result.get('title', '')} {result.get('excerpt', '')} {result.get('content', '')}"
        elif source_type == 'jira':
            text_content = f"{result.get('summary', '')} {result.get('description', '')}"
        elif source_type == 'code':
            text_content = f"{result.get('file_path', '')} {result.get('content_preview', '')}"
        else:
            return 0.5
        
        text_content_lower = text_content.lower()
        
        # Calculate different types of matches
        exact_matches = sum(1 for term in query_terms if term in text_content_lower)
        partial_matches = sum(1 for term in query_terms 
                            if any(term in word for word in text_content_lower.split()))
        
        # Title/summary matches get extra weight
        title_text = ""
        if source_type == 'confluence':
            title_text = result.get('title', '').lower()
        elif source_type == 'jira':
            title_text = result.get('summary', '').lower()
        elif source_type == 'code':
            title_text = result.get('file_path', '').lower()
        
        title_matches = sum(1 for term in query_terms if term in title_text)
        
        # Calculate relevance score
        if len(query_terms) == 0:
            return 0.5
        
        exact_score = exact_matches / len(query_terms)
        partial_score = partial_matches / len(query_terms) * 0.5
        title_score = title_matches / len(query_terms) * 1.5
        
        final_score = min(1.0, (exact_score + partial_score + title_score) / 2)
        return final_score
    
    def _calculate_recency_score(self, modified_date: str, created_date: str = None) -> float:
        """Calculate recency score based on modification and creation dates"""
        
        try:
            # Use modified date if available, otherwise created date
            date_str = modified_date or created_date
            if not date_str:
                return 0.5  # Neutral score if no date available
            
            # Parse date (handle various formats)
            content_date = self._parse_date(date_str)
            if not content_date:
                return 0.5
            
            # Calculate days since modification
            days_since = (datetime.now() - content_date).days
            
            # Scoring curve: 1.0 for today, 0.8 for 1 week, 0.6 for 1 month, 0.4 for 3 months, 0.2 for 1 year
            if days_since <= 1:
                return 1.0
            elif days_since <= 7:
                return 0.95 - (days_since - 1) * 0.025  # 0.95 to 0.8
            elif days_since <= 30:
                return 0.8 - (days_since - 7) * 0.0087  # 0.8 to 0.6
            elif days_since <= 90:
                return 0.6 - (days_since - 30) * 0.0033  # 0.6 to 0.4
            elif days_since <= 365:
                return 0.4 - (days_since - 90) * 0.0007  # 0.4 to 0.2
            else:
                return max(0.1, 0.2 - (days_since - 365) * 0.0001)  # 0.2 diminishing to 0.1
            
        except Exception as e:
            self.logger.debug(f"Error calculating recency score: {e}")
            return 0.5
    
    def _calculate_file_recency_score(self, result: Dict) -> float:
        """Calculate recency score for code files"""
        
        try:
            modified_timestamp = result.get('modified')
            if not modified_timestamp:
                return 0.5
            
            # Convert timestamp to datetime
            if isinstance(modified_timestamp, (int, float)):
                content_date = datetime.fromtimestamp(modified_timestamp)
            else:
                content_date = self._parse_date(str(modified_timestamp))
            
            if not content_date:
                return 0.5
            
            days_since = (datetime.now() - content_date).days
            
            # Similar scoring curve as other content
            if days_since <= 1:
                return 1.0
            elif days_since <= 7:
                return 0.9
            elif days_since <= 30:
                return 0.7
            elif days_since <= 90:
                return 0.5
            else:
                return max(0.2, 0.5 - (days_since - 90) * 0.001)
            
        except Exception as e:
            self.logger.debug(f"Error calculating file recency score: {e}")
            return 0.5
    
    def _calculate_team_relevance(self, result: Dict, user_context: Dict, source_type: str) -> float:
        """Calculate team-specific relevance score"""
        
        if not user_context:
            return 0.5
        
        score = 0.5  # Base score
        
        try:
            # Team-specific keywords
            team_keywords = user_context.get('team_keywords', [])
            if team_keywords:
                content_text = self._get_content_text(result, source_type).lower()
                matches = sum(1 for keyword in team_keywords if keyword.lower() in content_text)
                if team_keywords:
                    score += (matches / len(team_keywords)) * 0.3
            
            # User-specific context (assignee, author, etc.)
            if source_type == 'jira':
                assignee = result.get('assignee', '').lower()
                reporter = result.get('reporter', '').lower()
                current_user = user_context.get('username', '').lower()
                
                if current_user and (current_user in assignee or current_user in reporter):
                    score += 0.2
            
            elif source_type == 'confluence':
                author = result.get('author', '').lower()
                current_user = user_context.get('username', '').lower()
                
                if current_user and current_user in author:
                    score += 0.15
            
            # Project/space relevance
            if source_type == 'jira':
                project = result.get('project', '').lower()
                user_projects = [p.lower() for p in user_context.get('projects', [])]
                if project in user_projects:
                    score += 0.15
            
            elif source_type == 'confluence':
                space = result.get('space', '').lower()
                user_spaces = [s.lower() for s in user_context.get('spaces', [])]
                if space in user_spaces:
                    score += 0.15
            
        except Exception as e:
            self.logger.debug(f"Error calculating team relevance: {e}")
        
        return min(1.0, score)
    
    def _calculate_confluence_quality_score(self, result: Dict) -> float:
        """Calculate quality score for Confluence pages"""
        
        score = 0.5
        
        try:
            # Content length (longer content often more comprehensive)
            content_length = len(result.get('content', '') + result.get('excerpt', ''))
            if content_length > 1000:
                score += 0.2
            elif content_length > 500:
                score += 0.1
            
            # Page structure indicators
            title = result.get('title', '')
            if any(indicator in title.lower() for indicator in ['guide', 'documentation', 'how to', 'tutorial']):
                score += 0.15
            
            # Labels/tags present
            labels = result.get('labels', [])
            if labels and len(labels) > 0:
                score += 0.1
            
            # Recent updates (different from recency - indicates active maintenance)
            last_modified = result.get('last_modified', '')
            created = result.get('created', '')
            if last_modified and created and last_modified != created:
                score += 0.05  # Has been updated since creation
            
        except Exception as e:
            self.logger.debug(f"Error calculating Confluence quality score: {e}")
        
        return min(1.0, score)
    
    def _calculate_jira_quality_score(self, result: Dict) -> float:
        """Calculate quality score for JIRA issues"""
        
        score = 0.5
        
        try:
            # Description quality
            description = result.get('description', '')
            if len(description) > 100:
                score += 0.15
            
            # Has components
            components = result.get('components', [])
            if components:
                score += 0.1
            
            # Has labels
            labels = result.get('labels', [])
            if labels:
                score += 0.1
            
            # Priority relevance
            priority = result.get('priority', '').lower()
            if priority in ['high', 'critical', 'blocker']:
                score += 0.1
            elif priority in ['medium']:
                score += 0.05
            
            # Activity level (comments, updates)
            comments_count = len(result.get('comments', []))
            if comments_count > 0:
                score += min(0.1, comments_count * 0.02)
            
        except Exception as e:
            self.logger.debug(f"Error calculating JIRA quality score: {e}")
        
        return min(1.0, score)
    
    def _calculate_code_quality_score(self, result: Dict) -> float:
        """Calculate quality score for code files"""
        
        score = 0.5
        
        try:
            # File type importance
            file_path = result.get('file_path', '')
            file_extension = file_path.split('.')[-1].lower() if '.' in file_path else ''
            
            # Core code files get higher scores
            if file_extension in ['java', 'py', 'js', 'ts', 'cpp', 'c', 'go']:
                score += 0.15
            elif file_extension in ['sql', 'yaml', 'yml', 'json']:
                score += 0.1
            elif file_extension in ['md', 'txt']:
                score += 0.05
            
            # File location importance
            if any(important in file_path.lower() for important in ['src/main', 'lib/', 'core/', 'api/']):
                score += 0.1
            elif any(test in file_path.lower() for test in ['test/', 'spec/', '__test__']):
                score += 0.05  # Test files are useful but lower priority
            
            # File size (not too small, not too large)
            file_size = result.get('size', 0)
            if 1000 <= file_size <= 50000:  # 1KB to 50KB is good size
                score += 0.1
            elif 100 <= file_size <= 100000:  # 100B to 100KB is acceptable
                score += 0.05
            
            # Number of matches
            matches_count = len(result.get('matches', []))
            if matches_count > 0:
                score += min(0.15, matches_count * 0.03)
            
        except Exception as e:
            self.logger.debug(f"Error calculating code quality score: {e}")
        
        return min(1.0, score)
    
    def _calculate_cross_source_correlations(self, confluence_results: List[Dict], 
                                           jira_results: List[Dict], 
                                           code_results: List[Dict], 
                                           query: str) -> Dict[str, Any]:
        """Calculate correlations between results across different sources"""
        
        correlations = {
            'confluence_jira': [],
            'confluence_code': [],
            'jira_code': [],
            'strong_correlations': [],
            'correlation_insights': []
        }
        
        try:
            # Find correlations between Confluence and JIRA
            for conf_result in confluence_results[:10]:  # Limit to top 10 for performance
                for jira_result in jira_results[:10]:
                    correlation_score = self._calculate_correlation_score(
                        conf_result, jira_result, 'confluence', 'jira'
                    )
                    if correlation_score > 0.6:  # Threshold for correlation
                        correlations['confluence_jira'].append({
                            'confluence_id': conf_result.get('id'),
                            'jira_key': jira_result.get('key'),
                            'correlation_score': correlation_score,
                            'correlation_factors': self._identify_correlation_factors(
                                conf_result, jira_result, 'confluence', 'jira'
                            )
                        })
            
            # Find correlations between Confluence and Code
            for conf_result in confluence_results[:10]:
                for code_result in code_results[:15]:
                    correlation_score = self._calculate_correlation_score(
                        conf_result, code_result, 'confluence', 'code'
                    )
                    if correlation_score > 0.5:
                        correlations['confluence_code'].append({
                            'confluence_id': conf_result.get('id'),
                            'code_file': code_result.get('file_path'),
                            'correlation_score': correlation_score,
                            'correlation_factors': self._identify_correlation_factors(
                                conf_result, code_result, 'confluence', 'code'
                            )
                        })
            
            # Find correlations between JIRA and Code
            for jira_result in jira_results[:10]:
                for code_result in code_results[:15]:
                    correlation_score = self._calculate_correlation_score(
                        jira_result, code_result, 'jira', 'code'
                    )
                    if correlation_score > 0.5:
                        correlations['jira_code'].append({
                            'jira_key': jira_result.get('key'),
                            'code_file': code_result.get('file_path'),
                            'correlation_score': correlation_score,
                            'correlation_factors': self._identify_correlation_factors(
                                jira_result, code_result, 'jira', 'code'
                            )
                        })
            
            # Identify strong correlations across all sources
            all_correlations = (correlations['confluence_jira'] + 
                              correlations['confluence_code'] + 
                              correlations['jira_code'])
            
            correlations['strong_correlations'] = [
                corr for corr in all_correlations if corr['correlation_score'] > 0.75
            ]
            
            # Generate insights
            correlations['correlation_insights'] = self._generate_correlation_insights(correlations)
            
        except Exception as e:
            self.logger.error(f"Error calculating cross-source correlations: {e}")
        
        return correlations
    
    def _calculate_correlation_score(self, result1: Dict, result2: Dict, 
                                   type1: str, type2: str) -> float:
        """Calculate correlation score between two results from different sources"""
        
        try:
            # Extract text content
            text1 = self._get_content_text(result1, type1).lower()
            text2 = self._get_content_text(result2, type2).lower()
            
            # Extract key terms
            terms1 = set(re.findall(r'\b\w{3,}\b', text1))
            terms2 = set(re.findall(r'\b\w{3,}\b', text2))
            
            if not terms1 or not terms2:
                return 0.0
            
            # Calculate term overlap
            common_terms = terms1.intersection(terms2)
            term_overlap_score = len(common_terms) / max(len(terms1), len(terms2))
            
            # Look for specific correlation indicators
            correlation_indicators = 0.0
            
            # Technical terms correlation
            tech_terms = {'api', 'database', 'authentication', 'error', 'bug', 'feature', 'config', 'deploy'}
            tech_overlap = len(terms1.intersection(terms2).intersection(tech_terms))
            if tech_overlap > 0:
                correlation_indicators += tech_overlap * 0.1
            
            # Similar naming patterns
            if type1 == 'jira' and type2 == 'code':
                jira_key = result1.get('key', '')
                code_file = result2.get('file_path', '')
                if jira_key and any(part.lower() in code_file.lower() 
                                  for part in jira_key.split('-') if len(part) > 2):
                    correlation_indicators += 0.2
            
            # Date proximity (if both have dates)
            date_correlation = self._calculate_date_correlation(result1, result2, type1, type2)
            
            # Calculate final correlation score
            final_score = (term_overlap_score * 0.6 + 
                          correlation_indicators * 0.3 + 
                          date_correlation * 0.1)
            
            return min(1.0, final_score)
            
        except Exception as e:
            self.logger.debug(f"Error calculating correlation score: {e}")
            return 0.0
    
    def _apply_correlation_boosts(self, confluence_results: List[Dict], 
                                jira_results: List[Dict], 
                                code_results: List[Dict], 
                                correlations: Dict[str, Any]):
        """Apply ranking boosts based on cross-source correlations"""
        
        try:
            # Create correlation lookup maps
            correlation_boosts = defaultdict(float)
            
            # Process all correlations
            all_correlations = (correlations['confluence_jira'] + 
                              correlations['confluence_code'] + 
                              correlations['jira_code'])
            
            for corr in all_correlations:
                boost_amount = corr['correlation_score'] * 0.1  # Max 10% boost
                
                if 'confluence_id' in corr:
                    correlation_boosts[f"confluence_{corr['confluence_id']}"] += boost_amount
                if 'jira_key' in corr:
                    correlation_boosts[f"jira_{corr['jira_key']}"] += boost_amount
                if 'code_file' in corr:
                    correlation_boosts[f"code_{corr['code_file']}"] += boost_amount
            
            # Apply boosts to results
            for result in confluence_results:
                boost_key = f"confluence_{result.get('id')}"
                if boost_key in correlation_boosts:
                    original_score = result.get('ranking_score', 0.5)
                    boost = correlation_boosts[boost_key]
                    result['ranking_score'] = min(1.0, original_score + boost)
                    result['correlation_boost'] = boost
            
            for result in jira_results:
                boost_key = f"jira_{result.get('key')}"
                if boost_key in correlation_boosts:
                    original_score = result.get('ranking_score', 0.5)
                    boost = correlation_boosts[boost_key]
                    result['ranking_score'] = min(1.0, original_score + boost)
                    result['correlation_boost'] = boost
            
            for result in code_results:
                boost_key = f"code_{result.get('file_path')}"
                if boost_key in correlation_boosts:
                    original_score = result.get('ranking_score', 0.5)
                    boost = correlation_boosts[boost_key]
                    result['ranking_score'] = min(1.0, original_score + boost)
                    result['correlation_boost'] = boost
            
            # Re-sort results after applying boosts
            confluence_results.sort(key=lambda x: x.get('ranking_score', 0), reverse=True)
            jira_results.sort(key=lambda x: x.get('ranking_score', 0), reverse=True)
            code_results.sort(key=lambda x: x.get('ranking_score', 0), reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error applying correlation boosts: {e}")
    
    # Helper methods
    def _get_content_text(self, result: Dict, source_type: str) -> str:
        """Extract text content from result based on source type"""
        if source_type == 'confluence':
            return f"{result.get('title', '')} {result.get('excerpt', '')} {result.get('content', '')}"
        elif source_type == 'jira':
            return f"{result.get('summary', '')} {result.get('description', '')}"
        elif source_type == 'code':
            return f"{result.get('file_path', '')} {result.get('content_preview', '')}"
        return ""
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string in various formats"""
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _calculate_priority_boost(self, result: Dict) -> float:
        """Calculate priority boost for JIRA issues"""
        priority = result.get('priority', '').lower()
        priority_scores = {
            'blocker': 0.3,
            'critical': 0.25,
            'high': 0.2,
            'medium': 0.1,
            'low': 0.0
        }
        return priority_scores.get(priority, 0.05)
    
    def _calculate_status_relevance(self, result: Dict, query: str) -> float:
        """Calculate status relevance for JIRA issues based on query"""
        status = result.get('status', '').lower()
        query_lower = query.lower()
        
        # If query indicates looking for active issues
        if any(word in query_lower for word in ['current', 'active', 'working', 'progress']):
            if status in ['in progress', 'open', 'reopened']:
                return 0.2
        
        # If query indicates looking for resolved issues  
        if any(word in query_lower for word in ['resolved', 'fixed', 'completed', 'done']):
            if status in ['resolved', 'closed', 'done']:
                return 0.2
        
        return 0.1  # Default
    
    def _calculate_match_density(self, result: Dict, query: str) -> float:
        """Calculate match density for code files"""
        matches = result.get('matches', [])
        if not matches:
            return 0.0
        
        total_lines = result.get('lines', 1)
        match_density = len(matches) / max(total_lines, 1)
        return min(0.2, match_density * 10)  # Scale and cap at 0.2
    
    def _calculate_file_importance(self, result: Dict) -> float:
        """Calculate importance score for code files"""
        file_path = result.get('file_path', '').lower()
        
        # Important file patterns
        if any(pattern in file_path for pattern in ['main.', 'index.', 'app.', 'server.', 'config.']):
            return 0.15
        elif any(pattern in file_path for pattern in ['service', 'controller', 'manager', 'handler']):
            return 0.1
        elif any(pattern in file_path for pattern in ['util', 'helper', 'common']):
            return 0.05
        
        return 0.0
    
    def _calculate_date_correlation(self, result1: Dict, result2: Dict, type1: str, type2: str) -> float:
        """Calculate correlation based on date proximity"""
        try:
            date1 = None
            date2 = None
            
            # Extract dates based on type
            if type1 == 'confluence':
                date1 = self._parse_date(result1.get('last_modified') or result1.get('created'))
            elif type1 == 'jira':
                date1 = self._parse_date(result1.get('updated') or result1.get('created'))
            elif type1 == 'code':
                timestamp = result1.get('modified')
                if isinstance(timestamp, (int, float)):
                    date1 = datetime.fromtimestamp(timestamp)
            
            if type2 == 'confluence':
                date2 = self._parse_date(result2.get('last_modified') or result2.get('created'))
            elif type2 == 'jira':
                date2 = self._parse_date(result2.get('updated') or result2.get('created'))
            elif type2 == 'code':
                timestamp = result2.get('modified')
                if isinstance(timestamp, (int, float)):
                    date2 = datetime.fromtimestamp(timestamp)
            
            if not date1 or not date2:
                return 0.0
            
            # Calculate days difference
            days_diff = abs((date1 - date2).days)
            
            # Correlation score based on proximity
            if days_diff <= 1:
                return 1.0
            elif days_diff <= 7:
                return 0.8
            elif days_diff <= 30:
                return 0.6
            elif days_diff <= 90:
                return 0.4
            else:
                return 0.2
        
        except Exception as e:
            self.logger.debug(f"Error calculating date correlation: {e}")
            return 0.0
    
    def _identify_correlation_factors(self, result1: Dict, result2: Dict, type1: str, type2: str) -> List[str]:
        """Identify specific factors that contribute to correlation"""
        factors = []
        
        try:
            text1 = self._get_content_text(result1, type1).lower()
            text2 = self._get_content_text(result2, type2).lower()
            
            # Common technical terms
            tech_terms = set(['api', 'database', 'authentication', 'error', 'bug', 'feature', 'config', 'deploy'])
            terms1 = set(re.findall(r'\b\w{3,}\b', text1))
            terms2 = set(re.findall(r'\b\w{3,}\b', text2))
            
            common_tech = terms1.intersection(terms2).intersection(tech_terms)
            if common_tech:
                factors.append(f"Common technical terms: {', '.join(list(common_tech)[:3])}")
            
            # Date proximity
            date_corr = self._calculate_date_correlation(result1, result2, type1, type2)
            if date_corr > 0.6:
                factors.append("Similar timeframe")
            
            # Specific patterns
            if type1 == 'jira' and type2 == 'code':
                jira_key = result1.get('key', '')
                if jira_key and any(part.lower() in text2 for part in jira_key.split('-')):
                    factors.append("JIRA key referenced in code")
        
        except Exception as e:
            self.logger.debug(f"Error identifying correlation factors: {e}")
        
        return factors
    
    def _generate_correlation_insights(self, correlations: Dict[str, Any]) -> List[str]:
        """Generate human-readable insights about correlations"""
        insights = []
        
        try:
            total_correlations = len(correlations['confluence_jira'] + 
                                   correlations['confluence_code'] + 
                                   correlations['jira_code'])
            
            if total_correlations > 0:
                insights.append(f"Found {total_correlations} cross-source correlations")
            
            strong_count = len(correlations['strong_correlations'])
            if strong_count > 0:
                insights.append(f"{strong_count} strong correlations detected")
            
            if correlations['confluence_jira']:
                insights.append(f"{len(correlations['confluence_jira'])} documentation-issue correlations")
            
            if correlations['jira_code']:
                insights.append(f"{len(correlations['jira_code'])} issue-code correlations")
            
            if correlations['confluence_code']:
                insights.append(f"{len(correlations['confluence_code'])} documentation-code correlations")
        
        except Exception as e:
            self.logger.debug(f"Error generating correlation insights: {e}")
        
        return insights
    
    def _generate_ranking_insights(self, confluence_results: List[Dict], 
                                 jira_results: List[Dict], 
                                 code_results: List[Dict], 
                                 correlations: Dict[str, Any], 
                                 query: str) -> Dict[str, Any]:
        """Generate insights about the ranking process"""
        
        insights = {
            'total_results': len(confluence_results) + len(jira_results) + len(code_results),
            'ranking_summary': {},
            'top_factors': [],
            'correlation_summary': correlations.get('correlation_insights', []),
            'recommendations': []
        }
        
        try:
            # Analyze ranking factors across all results
            all_results = confluence_results + jira_results + code_results
            
            if all_results:
                avg_content_relevance = sum(r.get('ranking_breakdown', {}).get('content_relevance', 0) 
                                          for r in all_results) / len(all_results)
                avg_recency = sum(r.get('ranking_breakdown', {}).get('recency', 0) 
                                for r in all_results) / len(all_results)
                avg_quality = sum(r.get('ranking_breakdown', {}).get('quality_indicators', 0) 
                                for r in all_results) / len(all_results)
                
                insights['ranking_summary'] = {
                    'average_content_relevance': round(avg_content_relevance, 3),
                    'average_recency_score': round(avg_recency, 3),
                    'average_quality_score': round(avg_quality, 3)
                }
                
                # Top ranking factors
                if avg_content_relevance > 0.7:
                    insights['top_factors'].append("High content relevance")
                if avg_recency > 0.7:
                    insights['top_factors'].append("Recent content")
                if avg_quality > 0.7:
                    insights['top_factors'].append("High quality indicators")
                
                # Recommendations
                if avg_content_relevance < 0.5:
                    insights['recommendations'].append("Consider refining search terms for better content matching")
                if avg_recency < 0.4:
                    insights['recommendations'].append("Results are mostly older content - consider updating documentation")
                if len(correlations.get('strong_correlations', [])) > 3:
                    insights['recommendations'].append("Strong cross-source correlations found - check related items")
        
        except Exception as e:
            self.logger.error(f"Error generating ranking insights: {e}")
        
        return insights
    
    def _explain_ranking_factors(self, scores: Dict[str, float], source_type: str) -> List[str]:
        """Generate human-readable explanations for ranking factors"""
        explanations = []
        
        try:
            # Content relevance explanation
            content_score = scores.get('content_relevance', 0)
            if content_score > 0.8:
                explanations.append("Excellent keyword match")
            elif content_score > 0.6:
                explanations.append("Good keyword match")
            elif content_score > 0.4:
                explanations.append("Partial keyword match")
            else:
                explanations.append("Limited keyword match")
            
            # Recency explanation
            recency_score = scores.get('recency', 0)
            if recency_score > 0.9:
                explanations.append("Very recent content")
            elif recency_score > 0.7:
                explanations.append("Recent content")
            elif recency_score > 0.5:
                explanations.append("Moderately recent content")
            else:
                explanations.append("Older content")
            
            # Quality explanation
            quality_score = scores.get('quality_indicators', 0)
            if quality_score > 0.7:
                explanations.append("High quality indicators")
            elif quality_score > 0.5:
                explanations.append("Good quality indicators")
            
            # Source-specific explanations
            if source_type == 'jira':
                priority_boost = scores.get('priority_boost', 0)
                if priority_boost > 0.15:
                    explanations.append("High priority issue")
            
            elif source_type == 'code':
                match_density = scores.get('match_density', 0)
                if match_density > 0.1:
                    explanations.append("Multiple matches in file")
                    
                file_importance = scores.get('file_importance', 0)
                if file_importance > 0.1:
                    explanations.append("Important file type")
        
        except Exception as e:
            self.logger.debug(f"Error explaining ranking factors: {e}")
        
        return explanations