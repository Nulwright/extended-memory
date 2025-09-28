"""Validation Utilities"""

import re
from typing import List, Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)


def validate_memory_content(content: str) -> bool:
    """Validate memory content"""
    try:
        if not content:
            raise ValueError("Memory content cannot be empty")
        
        if not isinstance(content, str):
            raise ValueError("Memory content must be a string")
        
        # Check length constraints
        if len(content.strip()) < 5:
            raise ValueError("Memory content must be at least 5 characters long")
        
        if len(content) > 50000:
            raise ValueError("Memory content cannot exceed 50,000 characters")
        
        # Check for suspicious content
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'on\w+\s*=',  # Event handlers
        ]
        
        content_lower = content.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE | re.DOTALL):
                logger.warning("Potentially suspicious content detected in memory")
                # Don't reject, but log for security monitoring
                break
        
        return True
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Memory content validation failed: {e}")
        raise ValueError("Invalid memory content")


def validate_tags(tags: Optional[str]) -> bool:
    """Validate memory tags"""
    try:
        if tags is None or tags == "":
            return True  # Tags are optional
        
        if not isinstance(tags, str):
            raise ValueError("Tags must be a string")
        
        if len(tags) > 500:
            raise ValueError("Tags cannot exceed 500 characters")
        
        # Split tags and validate each one
        tag_list = [tag.strip() for tag in tags.split(',')]
        
        # Remove empty tags
        tag_list = [tag for tag in tag_list if tag]
        
        if len(tag_list) > 20:
            raise ValueError("Cannot have more than 20 tags")
        
        # Validate individual tags
        tag_pattern = re.compile(r'^[a-zA-Z0-9\-_\s]+)
        for tag in tag_list:
            if len(tag) > 50:
                raise ValueError("Individual tags cannot exceed 50 characters")
            
            if not tag_pattern.match(tag):
                raise ValueError("Tags can only contain letters, numbers, hyphens, underscores, and spaces")
        
        return True
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Tags validation failed: {e}")
        raise ValueError("Invalid tags format")


def validate_importance(importance: int) -> bool:
    """Validate importance score"""
    try:
        if not isinstance(importance, int):
            raise ValueError("Importance must be an integer")
        
        if importance < 1 or importance > 10:
            raise ValueError("Importance must be between 1 and 10")
        
        return True
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Importance validation failed: {e}")
        raise ValueError("Invalid importance value")


def validate_memory_type(memory_type: str) -> bool:
    """Validate memory type"""
    try:
        if not memory_type:
            raise ValueError("Memory type cannot be empty")
        
        if not isinstance(memory_type, str):
            raise ValueError("Memory type must be a string")
        
        valid_types = {
            'general', 'conversation', 'fact', 'task', 'project', 
            'personal', 'code', 'reference'
        }
        
        if memory_type not in valid_types:
            raise ValueError(f"Memory type must be one of: {', '.join(valid_types)}")
        
        return True
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Memory type validation failed: {e}")
        raise ValueError("Invalid memory type")


def validate_shared_category(shared_category: Optional[str], is_shared: bool) -> bool:
    """Validate shared category"""
    try:
        if not is_shared:
            return shared_category is None or shared_category == ""
        
        if is_shared and not shared_category:
            raise ValueError("Shared category is required when memory is shared")
        
        if not isinstance(shared_category, str):
            raise ValueError("Shared category must be a string")
        
        valid_categories = {
            'knowledge', 'tasks', 'projects', 'contacts', 'resources', 'templates'
        }
        
        if shared_category not in valid_categories:
            raise ValueError(f"Shared category must be one of: {', '.join(valid_categories)}")
        
        return True
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Shared category validation failed: {e}")
        raise ValueError("Invalid shared category")


def validate_assistant_name(name: str) -> bool:
    """Validate assistant name"""
    try:
        if not name:
            raise ValueError("Assistant name cannot be empty")
        
        if not isinstance(name, str):
            raise ValueError("Assistant name must be a string")
        
        name = name.strip()
        
        if len(name) < 1 or len(name) > 50:
            raise ValueError("Assistant name must be between 1 and 50 characters")
        
        # Allow letters, numbers, spaces, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9\s\-_]+, name):
            raise ValueError("Assistant name can only contain letters, numbers, spaces, hyphens, and underscores")
        
        # Must start with a letter
        if not name[0].isalpha():
            raise ValueError("Assistant name must start with a letter")
        
        return True
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Assistant name validation failed: {e}")
        raise ValueError("Invalid assistant name")


def validate_search_query(query: str) -> bool:
    """Validate search query"""
    try:
        if not query:
            raise ValueError("Search query cannot be empty")
        
        if not isinstance(query, str):
            raise ValueError("Search query must be a string")
        
        query = query.strip()
        
        if len(query) < 1:
            raise ValueError("Search query cannot be empty")
        
        if len(query) > 500:
            raise ValueError("Search query cannot exceed 500 characters")
        
        # Check for suspicious search patterns
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'SELECT\s+.*\s+FROM',  # SQL injection attempts
            r'UNION\s+SELECT',
            r'DROP\s+TABLE',
        ]
        
        query_lower = query.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                raise ValueError("Search query contains suspicious content")
        
        return True
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Search query validation failed: {e}")
        raise ValueError("Invalid search query")


def validate_email(email: str) -> bool:
    """Validate email address format"""
    try:
        if not email:
            return False
        
        if not isinstance(email, str):
            return False
        
        # Simple email validation pattern
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
        )
        
        return bool(email_pattern.match(email.strip()))
        
    except Exception as e:
        logger.error(f"Email validation failed: {e}")
        return False


def validate_pagination_params(skip: int, limit: int) -> bool:
    """Validate pagination parameters"""
    try:
        if not isinstance(skip, int) or not isinstance(limit, int):
            raise ValueError("Skip and limit must be integers")
        
        if skip < 0:
            raise ValueError("Skip must be non-negative")
        
        if limit <= 0:
            raise ValueError("Limit must be positive")
        
        if limit > 1000:
            raise ValueError("Limit cannot exceed 1000")
        
        return True
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Pagination validation failed: {e}")
        raise ValueError("Invalid pagination parameters")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage"""
    try:
        if not filename:
            return "unnamed"
        
        # Remove or replace unsafe characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove control characters
        filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
        
        # Limit length
        filename = filename[:255]
        
        # Ensure it's not empty after sanitization
        if not filename.strip():
            return "unnamed"
        
        return filename.strip()
        
    except Exception as e:
        logger.error(f"Filename sanitization failed: {e}")
        return "unnamed"


def validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> bool:
    """Validate date range parameters"""
    try:
        from esm.utils.date_utils import parse_flexible_date
        
        if start_date is None and end_date is None:
            return True  # No date range is valid
        
        parsed_start = None
        parsed_end = None
        
        if start_date:
            parsed_start = parse_flexible_date(start_date)
            if parsed_start is None:
                raise ValueError("Invalid start date format")
        
        if end_date:
            parsed_end = parse_flexible_date(end_date)
            if parsed_end is None:
                raise ValueError("Invalid end date format")
        
        if parsed_start and parsed_end and parsed_start > parsed_end:
            raise ValueError("Start date cannot be after end date")
        
        return True
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Date range validation failed: {e}")
        raise ValueError("Invalid date range")


def validate_export_format(format_type: str) -> bool:
    """Validate export format"""
    try:
        if not format_type:
            raise ValueError("Export format cannot be empty")
        
        valid_formats = {'json', 'csv', 'txt'}
        
        if format_type.lower() not in valid_formats:
            raise ValueError(f"Export format must be one of: {', '.join(valid_formats)}")
        
        return True
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Export format validation failed: {e}")
        raise ValueError("Invalid export format")
