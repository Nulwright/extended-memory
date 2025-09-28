"""Typesense Search Integration"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
import typesense
from typesense.exceptions import TypesenseClientError

from esm.config import get_settings
from esm.utils.exceptions import SearchError, ConfigurationError

logger = logging.getLogger(__name__)


class TypesenseClient:
    """Client for Typesense full-text search integration"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.collection_name = "esm_memories"
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Typesense client"""
        try:
            # Parse Typesense URL
            typesense_url = self.settings.typesense_url
            if typesense_url.startswith('http://'):
                protocol = 'http'
                host_port = typesense_url[7:]  # Remove 'http://'
            elif typesense_url.startswith('https://'):
                protocol = 'https'
                host_port = typesense_url[8:]  # Remove 'https://'
            else:
                protocol = 'http'
                host_port = typesense_url
            
            if ':' in host_port:
                host, port = host_port.split(':', 1)
                port = int(port)
            else:
                host = host_port
                port = 8108 if protocol == 'http' else 8109
            
            # Initialize client
            self.client = typesense.Client({
                'nodes': [{
                    'host': host,
                    'port': port,
                    'protocol': protocol
                }],
                'api_key': self.settings.typesense_api_key,
                'connection_timeout_seconds': 10
            })
            
            logger.info(f"Typesense client initialized: {host}:{port}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Typesense client: {e}")
            raise ConfigurationError(f"Typesense client initialization failed: {e}")
    
    async def initialize_collections(self):
        """Initialize Typesense collections"""
        try:
            if not self.client:
                raise SearchError("Typesense client not initialized")
            
            # Define memory collection schema
            memory_schema = {
                'name': self.collection_name,
                'fields': [
                    {'name': 'memory_id', 'type': 'int32'},
                    {'name': 'assistant_id', 'type': 'int32'},
                    {'name': 'assistant_name', 'type': 'string'},
                    {'name': 'content', 'type': 'string'},
                    {'name': 'summary', 'type': 'string', 'optional': True},
                    {'name': 'memory_type', 'type': 'string', 'facet': True},
                    {'name': 'importance', 'type': 'int32', 'facet': True},
                    {'name': 'tags', 'type': 'string[]', 'facet': True, 'optional': True},
                    {'name': 'is_shared', 'type': 'bool', 'facet': True},
                    {'name': 'shared_category', 'type': 'string', 'facet': True, 'optional': True},
                    {'name': 'created_timestamp', 'type': 'int64'},
                    {'name': 'access_count', 'type': 'int32'},
                ],
                'default_sorting_field': 'created_timestamp'
            }
            
            # Check if collection exists
            try:
                existing_collection = await asyncio.to_thread(
                    self.client.collections[self.collection_name].retrieve
                )
                logger.info(f"Collection '{self.collection_name}' already exists")
                
                # Update schema if needed (Typesense doesn't support schema updates directly)
                # For now, we'll just log and continue
                
            except TypesenseClientError as e:
                if 'Not Found' in str(e):
                    # Create collection
                    await asyncio.to_thread(
                        self.client.collections.create, 
                        memory_schema
                    )
                    logger.info(f"Created Typesense collection '{self.collection_name}'")
                else:
                    raise SearchError(f"Failed to check collection existence: {e}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Typesense collections: {e}")
            raise SearchError(f"Collection initialization failed: {e}")
    
    async def index_memory(self, memory_data: Dict[str, Any]):
        """Index a memory in Typesense"""
        try:
            if not self.client:
                raise SearchError("Typesense client not initialized")
            
            # Prepare document for indexing
            document = {
                'memory_id': memory_data['id'],
                'assistant_id': memory_data['assistant_id'],
                'assistant_name': memory_data.get('assistant_name', ''),
                'content': memory_data['content'] or '',
                'summary': memory_data.get('summary') or '',
                'memory_type': memory_data['memory_type'] or 'general',
                'importance': memory_data['importance'] or 5,
                'tags': self._parse_tags(memory_data.get('tags')),
                'is_shared': memory_data.get('is_shared', False),
                'shared_category': memory_data.get('shared_category') or '',
                'created_timestamp': int(memory_data['created_at'].timestamp()) if memory_data.get('created_at') else 0,
                'access_count': memory_data.get('access_count', 0)
            }
            
            # Index document
            await asyncio.to_thread(
                self.client.collections[self.collection_name].documents.upsert,
                document
            )
            
            logger.debug(f"Indexed memory {memory_data['id']} in Typesense")
            
        except Exception as e:
            logger.error(f"Failed to index memory {memory_data.get('id')}: {e}")
            # Don't raise exception to avoid breaking memory creation
    
    async def remove_memory(self, memory_id: int):
        """Remove a memory from Typesense index"""
        try:
            if not self.client:
                return
            
            await asyncio.to_thread(
                self.client.collections[self.collection_name].documents[str(memory_id)].delete
            )
            
            logger.debug(f"Removed memory {memory_id} from Typesense")
            
        except TypesenseClientError as e:
            if 'Not Found' not in str(e):
                logger.error(f"Failed to remove memory {memory_id} from Typesense: {e}")
        except Exception as e:
            logger.error(f"Failed to remove memory {memory_id} from Typesense: {e}")
    
    async def search_memories(
        self,
        query: str,
        assistant_id: Optional[int] = None,
        memory_type: Optional[str] = None,
        min_importance: Optional[int] = None,
        include_shared: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search memories in Typesense"""
        try:
            if not self.client:
                raise SearchError("Typesense client not initialized")
            
            # Build search parameters
            search_params = {
                'q': query or '*',
                'query_by': 'content,summary,tags',
                'sort_by': '_text_match:desc,importance:desc,created_timestamp:desc',
                'per_page': min(limit, 250),  # Typesense limit
                'page': 1
            }
            
            # Build filter conditions
            filter_conditions = []
            
            # Assistant filter
            if assistant_id:
                if include_shared:
                    filter_conditions.append(f'(assistant_id:={assistant_id} || is_shared:=true)')
                else:
                    filter_conditions.append(f'assistant_id:={assistant_id}')
            elif not include_shared:
                # This is an edge case - no assistant specified but shared excluded
                return []
            
            # Memory type filter
            if memory_type:
                filter_conditions.append(f'memory_type:={memory_type}')
            
            # Importance filter
            if min_importance:
                filter_conditions.append(f'importance:>={min_importance}')
            
            # Combine filters
            if filter_conditions:
                search_params['filter_by'] = ' && '.join(filter_conditions)
            
            # Perform search
            search_results = await asyncio.to_thread(
                self.client.collections[self.collection_name].documents.search,
                search_params
            )
            
            # Process results
            results = []
            for hit in search_results.get('hits', []):
                document = hit.get('document', {})
                
                result = {
                    'memory_id': document.get('memory_id'),
                    'score': hit.get('text_match_info', {}).get('score', 0),
                    'highlights': hit.get('highlights', [])
                }
                
                results.append(result)
            
            logger.debug(f"Typesense search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Typesense search failed for query '{query}': {e}")
            raise SearchError(f"Search operation failed: {e}", query)
    
    async def get_search_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """Get search suggestions from Typesense"""
        try:
            if not self.client or not query:
                return []
            
            # Use Typesense's prefix search for suggestions
            search_params = {
                'q': query,
                'query_by': 'content,summary',
                'prefix': 'true',
                'per_page': limit,
                'include_fields': 'content'
            }
            
            search_results = await asyncio.to_thread(
                self.client.collections[self.collection_name].documents.search,
                search_params
            )
            
            suggestions = []
            for hit in search_results.get('hits', []):
                # Extract suggestions from highlights or content
                highlights = hit.get('highlights', [])
                for highlight in highlights:
                    if highlight.get('field') in ['content', 'summary']:
                        # Simple suggestion extraction (could be improved)
                        snippet = highlight.get('snippet', '')
                        # Extract words around the query
                        words = snippet.split()
                        suggestions.extend(words[:3])  # Take first few words
            
            # Remove duplicates and return unique suggestions
            unique_suggestions = list(set(suggestions))
            return unique_suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get search suggestions: {e}")
            return []
    
    async def get_facets(self, field: str) -> Dict[str, int]:
        """Get facet counts for a field"""
        try:
            if not self.client:
                return {}
            
            search_params = {
                'q': '*',
                'query_by': 'content',
                'facet_by': field,
                'per_page': 0  # Don't return documents, just facets
            }
            
            search_results = await asyncio.to_thread(
                self.client.collections[self.collection_name].documents.search,
                search_params
            )
            
            facets = {}
            facet_counts = search_results.get('facet_counts', [])
            
            for facet in facet_counts:
                if facet.get('field_name') == field:
                    for count_info in facet.get('counts', []):
                        facets[count_info.get('value')] = count_info.get('count', 0)
                    break
            
            return facets
            
        except Exception as e:
            logger.error(f"Failed to get facets for field '{field}': {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Typesense service health"""
        try:
            if not self.client:
                return {"status": "unavailable", "error": "Client not initialized"}
            
            # Test connection with a simple operation
            health_info = await asyncio.to_thread(self.client.health.retrieve)
            
            # Get collection info
            collection_info = await asyncio.to_thread(
                self.client.collections[self.collection_name].retrieve
            )
            
            return {
                "status": "healthy",
                "service": "typesense",
                "url": self.settings.typesense_url,
                "collection": self.collection_name,
                "documents": collection_info.get('num_documents', 0),
                "health": health_info
            }
            
        except Exception as e:
            logger.error(f"Typesense health check failed: {e}")
            return {
                "status": "unhealthy", 
                "error": str(e),
                "service": "typesense"
            }
    
    def _parse_tags(self, tags_str: Optional[str]) -> List[str]:
        """Parse tags string into list"""
        if not tags_str:
            return []
        
        try:
            # Split by comma and clean up
            tags = [tag.strip() for tag in tags_str.split(',')]
            return [tag for tag in tags if tag]
        except Exception:
            return []
