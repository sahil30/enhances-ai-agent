import asyncio
import json
import pickle
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SearchResult:
    """Individual search result with relevance scoring"""
    content: str
    source: str
    source_type: str  # confluence, jira, code
    title: str
    url: Optional[str] = None
    metadata: Dict[str, Any] = None
    relevance_score: float = 0.0
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    freshness_score: float = 0.0
    popularity_score: float = 0.0
    combined_score: float = 0.0


@dataclass
class SearchIndex:
    """Search index for a specific content type"""
    vectorizer: TfidfVectorizer
    tfidf_matrix: np.ndarray
    svd_model: Optional[TruncatedSVD]
    reduced_matrix: Optional[np.ndarray]
    documents: List[Dict[str, Any]]
    document_embeddings: Dict[str, np.ndarray]


class SemanticSearchEngine:
    """Advanced semantic search with multiple ranking algorithms"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.indexes: Dict[str, SearchIndex] = {}
        
        # Search configuration
        self.max_features = config.get('max_features', 10000)
        self.ngram_range = config.get('ngram_range', (1, 3))
        self.svd_components = config.get('svd_components', 300)
        self.min_df = config.get('min_df', 2)
        self.max_df = config.get('max_df', 0.8)
        
        # Scoring weights
        self.score_weights = {
            'semantic': config.get('semantic_weight', 0.4),
            'keyword': config.get('keyword_weight', 0.3),
            'freshness': config.get('freshness_weight', 0.15),
            'popularity': config.get('popularity_weight', 0.15)
        }
        
        # Cache for query embeddings
        self.query_cache: Dict[str, np.ndarray] = {}
        
    async def build_index(self, documents: List[Dict[str, Any]], source_type: str) -> bool:
        """Build search index for a document collection"""
        try:
            logger.info(f"Building search index for {source_type} with {len(documents)} documents")
            
            if not documents:
                logger.warning(f"No documents to index for {source_type}")
                return False
            
            # Extract text content for indexing
            texts = []
            processed_docs = []
            
            for doc in documents:
                text_content = self._extract_text_content(doc, source_type)
                if text_content and len(text_content.strip()) > 10:  # Minimum content length
                    texts.append(text_content)
                    processed_docs.append(doc)
            
            if not texts:
                logger.warning(f"No valid text content found for {source_type}")
                return False
            
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                max_features=self.max_features,
                ngram_range=self.ngram_range,
                min_df=self.min_df,
                max_df=self.max_df,
                stop_words='english',
                lowercase=True,
                strip_accents='ascii'
            )
            
            # Fit and transform documents
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Apply dimensionality reduction for semantic similarity
            svd_model = None
            reduced_matrix = None
            
            if tfidf_matrix.shape[1] > self.svd_components:
                svd_model = TruncatedSVD(n_components=self.svd_components, random_state=42)
                reduced_matrix = svd_model.fit_transform(tfidf_matrix)
                reduced_matrix = normalize(reduced_matrix, norm='l2')
            
            # Create document embeddings dictionary
            document_embeddings = {}
            for i, doc in enumerate(processed_docs):
                doc_id = self._get_document_id(doc, source_type)
                if reduced_matrix is not None:
                    document_embeddings[doc_id] = reduced_matrix[i]
                else:
                    document_embeddings[doc_id] = tfidf_matrix[i].toarray().flatten()
            
            # Store index
            self.indexes[source_type] = SearchIndex(
                vectorizer=vectorizer,
                tfidf_matrix=tfidf_matrix,
                svd_model=svd_model,
                reduced_matrix=reduced_matrix,
                documents=processed_docs,
                document_embeddings=document_embeddings
            )
            
            logger.info(f"Search index built successfully for {source_type}: "
                       f"{len(processed_docs)} documents, "
                       f"{tfidf_matrix.shape[1]} features")
            
            return True
            
        except Exception as e:
            logger.error(f"Error building search index for {source_type}: {e}")
            return False
    
    async def search(self, 
                    query: str, 
                    source_types: Optional[List[str]] = None,
                    limit: int = 20,
                    min_score: float = 0.1) -> List[SearchResult]:
        """Perform semantic search across specified sources"""
        
        if source_types is None:
            source_types = list(self.indexes.keys())
        
        logger.debug(f"Searching for: '{query}' in sources: {source_types}")
        
        all_results = []
        
        # Search each source type
        for source_type in source_types:
            if source_type not in self.indexes:
                logger.warning(f"No index found for source type: {source_type}")
                continue
            
            results = await self._search_index(query, source_type, limit * 2)  # Get more for reranking
            all_results.extend(results)
        
        # Sort by combined score and apply limit
        all_results.sort(key=lambda x: x.combined_score, reverse=True)
        
        # Filter by minimum score
        filtered_results = [r for r in all_results if r.combined_score >= min_score]
        
        logger.info(f"Search completed: {len(filtered_results)} results found")
        
        return filtered_results[:limit]
    
    async def _search_index(self, query: str, source_type: str, limit: int) -> List[SearchResult]:
        """Search within a specific index"""
        index = self.indexes[source_type]
        
        try:
            # Transform query using the same vectorizer
            query_tfidf = index.vectorizer.transform([query])
            
            # Get semantic embedding
            if index.svd_model and index.reduced_matrix is not None:
                query_embedding = index.svd_model.transform(query_tfidf)
                query_embedding = normalize(query_embedding, norm='l2')
                similarity_matrix = index.reduced_matrix
            else:
                query_embedding = query_tfidf.toarray()
                similarity_matrix = index.tfidf_matrix
            
            # Calculate similarities
            similarities = cosine_similarity(query_embedding, similarity_matrix).flatten()
            
            # Get top results
            top_indices = np.argsort(similarities)[::-1][:limit]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0:  # Only include non-zero similarities
                    doc = index.documents[idx]
                    
                    # Create search result
                    result = SearchResult(
                        content=self._extract_text_content(doc, source_type),
                        source=self._get_document_id(doc, source_type),
                        source_type=source_type,
                        title=self._extract_title(doc, source_type),
                        url=self._extract_url(doc, source_type),
                        metadata=self._extract_metadata(doc, source_type),
                        semantic_score=float(similarities[idx])
                    )
                    
                    # Calculate additional scores
                    result.keyword_score = self._calculate_keyword_score(query, result.content)
                    result.freshness_score = self._calculate_freshness_score(result.metadata)
                    result.popularity_score = self._calculate_popularity_score(result.metadata)
                    
                    # Calculate combined score
                    result.combined_score = self._calculate_combined_score(result)
                    
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching index {source_type}: {e}")
            return []
    
    async def find_similar_documents(self, 
                                   document_id: str, 
                                   source_type: str,
                                   limit: int = 10) -> List[SearchResult]:
        """Find documents similar to a given document"""
        
        if source_type not in self.indexes:
            return []
        
        index = self.indexes[source_type]
        
        if document_id not in index.document_embeddings:
            return []
        
        try:
            # Get document embedding
            doc_embedding = index.document_embeddings[document_id]
            
            # Calculate similarities with all other documents
            if index.reduced_matrix is not None:
                similarities = cosine_similarity([doc_embedding], index.reduced_matrix).flatten()
            else:
                similarities = cosine_similarity([doc_embedding], index.tfidf_matrix).flatten()
            
            # Get top similar documents (excluding self)
            top_indices = np.argsort(similarities)[::-1]
            
            results = []
            for idx in top_indices:
                if len(results) >= limit:
                    break
                
                # Skip self
                current_doc_id = self._get_document_id(index.documents[idx], source_type)
                if current_doc_id == document_id:
                    continue
                
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    doc = index.documents[idx]
                    
                    result = SearchResult(
                        content=self._extract_text_content(doc, source_type),
                        source=current_doc_id,
                        source_type=source_type,
                        title=self._extract_title(doc, source_type),
                        url=self._extract_url(doc, source_type),
                        metadata=self._extract_metadata(doc, source_type),
                        semantic_score=float(similarities[idx]),
                        combined_score=float(similarities[idx])
                    )
                    
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error finding similar documents: {e}")
            return []
    
    def _extract_text_content(self, doc: Dict[str, Any], source_type: str) -> str:
        """Extract searchable text content from document"""
        if source_type == 'confluence':
            content_parts = [
                doc.get('title', ''),
                doc.get('excerpt', ''),
                doc.get('content', ''),
                doc.get('space', '')
            ]
        elif source_type == 'jira':
            content_parts = [
                doc.get('key', ''),
                doc.get('summary', ''),
                doc.get('description', ''),
                doc.get('status', ''),
                doc.get('priority', '')
            ]
        elif source_type == 'code':
            content_parts = [
                doc.get('file_path', ''),
                doc.get('content_preview', ''),
                str(doc.get('analysis', {}))
            ]
        else:
            # Generic extraction
            content_parts = [str(v) for v in doc.values() if isinstance(v, (str, int, float))]
        
        return ' '.join(filter(None, content_parts))
    
    def _get_document_id(self, doc: Dict[str, Any], source_type: str) -> str:
        """Generate unique document ID"""
        if source_type == 'confluence':
            return f"confluence:{doc.get('id', doc.get('title', 'unknown'))}"
        elif source_type == 'jira':
            return f"jira:{doc.get('key', doc.get('id', 'unknown'))}"
        elif source_type == 'code':
            return f"code:{doc.get('file_path', 'unknown')}"
        else:
            return f"{source_type}:{doc.get('id', hash(str(doc)))}"
    
    def _extract_title(self, doc: Dict[str, Any], source_type: str) -> str:
        """Extract document title"""
        if source_type == 'confluence':
            return doc.get('title', 'Untitled')
        elif source_type == 'jira':
            return f"{doc.get('key', '')}: {doc.get('summary', 'Untitled')}"
        elif source_type == 'code':
            return doc.get('file_path', 'Unknown file')
        else:
            return doc.get('title', doc.get('name', 'Untitled'))
    
    def _extract_url(self, doc: Dict[str, Any], source_type: str) -> Optional[str]:
        """Extract document URL"""
        return doc.get('url')
    
    def _extract_metadata(self, doc: Dict[str, Any], source_type: str) -> Dict[str, Any]:
        """Extract document metadata for scoring"""
        metadata = {}
        
        if source_type == 'confluence':
            metadata.update({
                'last_modified': doc.get('lastModified'),
                'space': doc.get('space'),
                'version': doc.get('version')
            })
        elif source_type == 'jira':
            metadata.update({
                'created': doc.get('created'),
                'updated': doc.get('updated'),
                'status': doc.get('status'),
                'priority': doc.get('priority'),
                'assignee': doc.get('assignee')
            })
        elif source_type == 'code':
            metadata.update({
                'file_type': doc.get('file_type'),
                'size': doc.get('size'),
                'modified': doc.get('modified'),
                'matches': doc.get('matches', [])
            })
        
        return metadata
    
    def _calculate_keyword_score(self, query: str, content: str) -> float:
        """Calculate keyword matching score"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words:
            return 0.0
        
        # Exact matches
        exact_matches = len(query_words.intersection(content_words))
        
        # Partial matches (substring matching)
        partial_matches = 0
        for query_word in query_words:
            if any(query_word in content_word for content_word in content_words):
                partial_matches += 1
        
        # Combined score
        exact_score = exact_matches / len(query_words)
        partial_score = partial_matches / len(query_words) * 0.5
        
        return min(1.0, exact_score + partial_score)
    
    def _calculate_freshness_score(self, metadata: Dict[str, Any]) -> float:
        """Calculate freshness score based on document age"""
        import time
        from datetime import datetime
        
        current_time = time.time()
        
        # Try to find a timestamp in metadata
        timestamp_fields = ['last_modified', 'updated', 'modified', 'created']
        doc_time = None
        
        for field in timestamp_fields:
            value = metadata.get(field)
            if value:
                try:
                    if isinstance(value, str):
                        # Try parsing common date formats
                        for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                            try:
                                doc_time = datetime.strptime(value.split('.')[0], fmt).timestamp()
                                break
                            except ValueError:
                                continue
                    elif isinstance(value, (int, float)):
                        doc_time = value
                    
                    if doc_time:
                        break
                except Exception:
                    continue
        
        if not doc_time:
            return 0.5  # Neutral score if no timestamp found
        
        # Calculate age in days
        age_seconds = current_time - doc_time
        age_days = age_seconds / (24 * 3600)
        
        # Fresher documents get higher scores
        if age_days < 7:
            return 1.0
        elif age_days < 30:
            return 0.8
        elif age_days < 90:
            return 0.6
        elif age_days < 365:
            return 0.4
        else:
            return 0.2
    
    def _calculate_popularity_score(self, metadata: Dict[str, Any]) -> float:
        """Calculate popularity score based on usage indicators"""
        score = 0.0
        
        # Code file popularity indicators
        if 'matches' in metadata:
            match_count = len(metadata['matches'])
            score += min(1.0, match_count / 10) * 0.5
        
        # File size as complexity indicator
        if 'size' in metadata:
            size = metadata['size']
            if 1000 < size < 100000:  # Sweet spot for code files
                score += 0.3
        
        # JIRA priority
        if 'priority' in metadata:
            priority = str(metadata['priority']).lower()
            priority_scores = {'critical': 1.0, 'high': 0.8, 'medium': 0.6, 'low': 0.4}
            score += priority_scores.get(priority, 0.5) * 0.2
        
        return min(1.0, score)
    
    def _calculate_combined_score(self, result: SearchResult) -> float:
        """Calculate combined relevance score"""
        return (
            result.semantic_score * self.score_weights['semantic'] +
            result.keyword_score * self.score_weights['keyword'] +
            result.freshness_score * self.score_weights['freshness'] +
            result.popularity_score * self.score_weights['popularity']
        )
    
    async def save_index(self, source_type: str, file_path: str) -> bool:
        """Save search index to disk"""
        if source_type not in self.indexes:
            return False
        
        try:
            index = self.indexes[source_type]
            
            # Prepare data for serialization
            index_data = {
                'vectorizer': index.vectorizer,
                'tfidf_matrix': index.tfidf_matrix,
                'svd_model': index.svd_model,
                'reduced_matrix': index.reduced_matrix,
                'documents': index.documents,
                'document_embeddings': index.document_embeddings
            }
            
            with open(file_path, 'wb') as f:
                pickle.dump(index_data, f)
            
            logger.info(f"Index for {source_type} saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving index for {source_type}: {e}")
            return False
    
    async def load_index(self, source_type: str, file_path: str) -> bool:
        """Load search index from disk"""
        try:
            with open(file_path, 'rb') as f:
                index_data = pickle.load(f)
            
            self.indexes[source_type] = SearchIndex(**index_data)
            
            logger.info(f"Index for {source_type} loaded from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading index for {source_type}: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics about all indexes"""
        stats = {}
        
        for source_type, index in self.indexes.items():
            stats[source_type] = {
                'document_count': len(index.documents),
                'vocabulary_size': len(index.vectorizer.vocabulary_) if hasattr(index.vectorizer, 'vocabulary_') else 0,
                'feature_count': index.tfidf_matrix.shape[1] if index.tfidf_matrix is not None else 0,
                'has_svd': index.svd_model is not None,
                'svd_components': index.reduced_matrix.shape[1] if index.reduced_matrix is not None else 0
            }
        
        return stats


# Global semantic search engine instance
search_config = {
    'max_features': 10000,
    'ngram_range': (1, 3),
    'svd_components': 300,
    'semantic_weight': 0.4,
    'keyword_weight': 0.3,
    'freshness_weight': 0.15,
    'popularity_weight': 0.15
}

semantic_search = SemanticSearchEngine(search_config)


async def enhance_search_results(results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """Enhance search results using semantic search engine"""
    try:
        # Convert results to SearchResult objects for processing
        search_results = []
        for result in results:
            search_result = SearchResult(
                content=str(result.get('content', '')),
                source=str(result.get('source', '')),
                source_type=str(result.get('source_type', 'unknown')),
                title=str(result.get('title', '')),
                url=result.get('url'),
                metadata=result.get('metadata', {}),
                relevance_score=float(result.get('relevance_score', 0.0))
            )
            
            # Calculate enhanced scores
            search_result.keyword_score = semantic_search._calculate_keyword_score(query, search_result.content)
            search_result.freshness_score = semantic_search._calculate_freshness_score(search_result.metadata)
            search_result.popularity_score = semantic_search._calculate_popularity_score(search_result.metadata)
            search_result.combined_score = semantic_search._calculate_combined_score(search_result)
            
            search_results.append(search_result)
        
        # Sort by combined score
        search_results.sort(key=lambda x: x.combined_score, reverse=True)
        
        # Convert back to dictionary format
        enhanced_results = []
        for search_result in search_results:
            enhanced_result = {
                'content': search_result.content,
                'source': search_result.source,
                'source_type': search_result.source_type,
                'title': search_result.title,
                'url': search_result.url,
                'metadata': search_result.metadata,
                'relevance_score': search_result.relevance_score,
                'semantic_score': search_result.semantic_score,
                'keyword_score': search_result.keyword_score,
                'freshness_score': search_result.freshness_score,
                'popularity_score': search_result.popularity_score,
                'combined_score': search_result.combined_score
            }
            enhanced_results.append(enhanced_result)
        
        return enhanced_results
        
    except Exception as e:
        logger.error(f"Error enhancing search results: {e}")
        return results  # Return original results on error