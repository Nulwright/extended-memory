```python
"""Export Service for Data Export Operations"""

import asyncio
import json
import csv
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import tempfile

from esm.models import Memory, Assistant
from esm.schemas import ExportRequest, MemoryResponse
from esm.database import get_db_context

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting memory data"""
    
    def __init__(self):
        self.export_dir = Path("data/exports")
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        # Track active exports
        self.active_exports = {}
    
    async def create_export(self, export_request: ExportRequest) -> Dict[str, Any]:
        """Create a new export job"""
        try:
            export_id = str(uuid.uuid4())
            
            # Store export info
            export_info = {
                "export_id": export_id,
                "status": "pending",
                "format": export_request.format,
                "assistant_id": export_request.assistant_id,
                "include_shared": export_request.include_shared,
                "memory_type": export_request.memory_type,
                "date_from": export_request.date_from,
                "date_to": export_request.date_to,
                "created_at": datetime.utcnow(),
                "file_url": f"/api/v1/export/{export_id}/download",
                "file_size": 0,
                "record_count": 0
            }
            
            self.active_exports[export_id] = export_info
            
            logger.info(f"Created export job {export_id}")
            return export_info
            
        except Exception as e:
            logger.error(f"Failed to create export: {e}")
            raise
    
    async def generate_export_file(self, export_id: str, export_request: ExportRequest):
        """Generate export file (background task)"""
        try:
            if export_id not in self.active_exports:
                logger.error(f"Export {export_id} not found")
                return
            
            # Update status
            self.active_exports[export_id]["status"] = "processing"
            
            # Fetch data
            memories = await self._fetch_export_data(export_request)
            
            # Generate file based on format
            if export_request.format == "json":
                file_path = await self._generate_json_export(export_id, memories)
            elif export_request.format == "csv":
                file_path = await self._generate_csv_export(export_id, memories)
            elif export_request.format == "txt":
                file_path = await self._generate_txt_export(export_id, memories)
            else:
                raise ValueError(f"Unsupported export format: {export_request.format}")
            
            # Update export info
            file_size = Path(file_path).stat().st_size
            self.active_exports[export_id].update({
                "status": "completed",
                "file_path": str(file_path),
                "file_size": file_size,
                "record_count": len(memories),
                "completed_at": datetime.utcnow()
            })
            
            logger.info(f"Export {export_id} completed: {len(memories)} records, {file_size} bytes")
            
        except Exception as e:
            logger.error(f"Export {export_id} failed: {e}")
            if export_id in self.active_exports:
                self.active_exports[export_id]["status"] = "failed"
                self.active_exports[export_id]["error"] = str(e)
    
    async def generate_export_immediately(self, export_request: ExportRequest) -> str:
        """Generate export file immediately (not as background task)"""
        try:
            export_id = str(uuid.uuid4())
            
            # Fetch data
            memories = await self._fetch_export_data(export_request)
            
            # Generate file based on format
            if export_request.format == "json":
                file_path = await self._generate_json_export(export_id, memories)
            elif export_request.format == "csv":
                file_path = await self._generate_csv_export(export_id, memories)
            elif export_request.format == "txt":
                file_path = await self._generate_txt_export(export_id, memories)
            else:
                raise ValueError(f"Unsupported export format: {export_request.format}")
            
            logger.info(f"Immediate export completed: {len(memories)} records")
            return file_path
            
        except Exception as e:
            logger.error(f"Immediate export failed: {e}")
            raise
    
    async def _fetch_export_data(self, export_request: ExportRequest) -> List[Dict[str, Any]]:
        """Fetch data for export"""
        try:
            with get_db_context() as db:
                query = db.query(Memory).join(Assistant)
                
                # Filter by assistant if specified
                if export_request.assistant_id:
                    if export_request.include_shared:
                        from sqlalchemy import or_
                        query = query.filter(
                            or_(
                                Memory.assistant_id == export_request.assistant_id,
                                Memory.is_shared == True
                            )
                        )
                    else:
                        query = query.filter(Memory.assistant_id == export_request.assistant_id)
                elif not export_request.include_shared:
                    # If no assistant specified and shared not included, return empty
                    return []
                
                # Filter by memory type
                if export_request.memory_type:
                    query = query.filter(Memory.memory_type == export_request.memory_type)
                
                # Filter by date range
                if export_request.date_from:
                    query = query.filter(Memory.created_at >= export_request.date_from)
                
                if export_request.date_to:
                    query = query.filter(Memory.created_at <= export_request.date_to)
                
                # Order by creation date
                query = query.order_by(Memory.created_at)
                
                memories = query.all()
                
                # Convert to export format
                export_data = []
                for memory in memories:
                    export_data.append({
                        "id": memory.id,
                        "assistant_id": memory.assistant_id,
                        "assistant_name": memory.assistant.name,
                        "content": memory.content,
                        "summary": memory.summary,
                        "memory_type": memory.memory_type,
                        "importance": memory.importance,
                        "tags": memory.tags,
                        "source": memory.source,
                        "context": memory.context,
                        "is_shared": memory.is_shared,
                        "shared_category": memory.shared_category,
                        "access_count": memory.access_count or 0,
                        "created_at": memory.created_at.isoformat(),
                        "updated_at": memory.updated_at.isoformat(),
                        "accessed_at": memory.accessed_at.isoformat() if memory.accessed_at else None
                    })
                
                return export_data
                
        except Exception as e:
            logger.error(f"Failed to fetch export data: {e}")
            raise
    
    async def _generate_json_export(self, export_id: str, memories: List[Dict]) -> str:
        """Generate JSON export file"""
        try:
            file_path = self.export_dir / f"export_{export_id}.json"
            
            export_data = {
                "export_metadata": {
                    "export_id": export_id,
                    "export_format": "json",
                    "generated_at": datetime.utcnow().isoformat(),
                    "record_count": len(memories),
                    "version": "1.0"
                },
                "memories": memories
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to generate JSON export: {e}")
            raise
    
    async def _generate_csv_export(self, export_id: str, memories: List[Dict]) -> str:
        """Generate CSV export file"""
        try:
            file_path = self.export_dir / f"export_{export_id}.csv"
            
            if not memories:
                # Create empty CSV with headers
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['id', 'assistant_name', 'content', 'memory_type', 'importance', 'created_at'])
                return str(file_path)
            
            # Get all possible field names
            fieldnames = set()
            for memory in memories:
                fieldnames.update(memory.keys())
            
            fieldnames = sorted(list(fieldnames))
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for memory in memories:
                    # Clean data for CSV
                    clean_memory = {}
                    for key, value in memory.items():
                        if value is None:
                            clean_memory[key] = ""
                        elif isinstance(value, (list, dict)):
                            clean_memory[key] = json.dumps(value)
                        else:
                            clean_memory[key] = str(value)
                    
                    writer.writerow(clean_memory)
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to generate CSV export: {e}")
            raise
    
    async def _generate_txt_export(self, export_id: str, memories: List[Dict]) -> str:
        """Generate plain text export file"""
        try:
            file_path = self.export_dir / f"export_{export_id}.txt"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"ESM Memory Export\n")
                f.write(f"Generated: {datetime.utcnow().isoformat()}\n")
                f.write(f"Total Records: {len(memories)}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, memory in enumerate(memories, 1):
                    f.write(f"Memory #{i}\n")
                    f.write(f"ID: {memory['id']}\n")
                    f.write(f"Assistant: {memory['assistant_name']}\n")
                    f.write(f"Type: {memory['memory_type']}\n")
                    f.write(f"Importance: {memory['importance']}/10\n")
                    f.write(f"Created: {memory['created_at']}\n")
                    
                    if memory['tags']:
                        f.write(f"Tags: {memory['tags']}\n")
                    
                    if memory['is_shared']:
                        f.write(f"Shared: Yes ({memory['shared_category']})\n")
                    
                    f.write(f"\nContent:\n{memory['content']}\n")
                    
                    if memory['summary']:
                        f.write(f"\nSummary:\n{memory['summary']}\n")
                    
                    if memory['context']:
                        f.write(f"\nContext:\n{memory['context']}\n")
                    
                    f.write("\n" + "-" * 80 + "\n\n")
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to generate TXT export: {e}")
            raise
    
    async def get_export_status(self, export_id: str) -> Optional[Dict[str, Any]]:
        """Get export job status"""
        return self.active_exports.get(export_id)
    
    async def get_export_file_path(self, export_id: str) -> Optional[str]:
        """Get export file path if ready"""
        export_info = self.active_exports.get(export_id)
        if export_info and export_info["status"] == "completed":
            return export_info.get("file_path")
        return None
    
    async def delete_export(self, export_id: str) -> bool:
        """Delete export and its file"""
        try:
            if export_id not in self.active_exports:
                return False
            
            export_info = self.active_exports[export_id]
            
            # Delete file if it exists
            if "file_path" in export_info:
                file_path = Path(export_info["file_path"])
                if file_path.exists():
                    file_path.unlink()
            
            # Remove from active exports
            del self.active_exports[export_id]
            
            logger.info(f"Deleted export {export_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete export {export_id}: {e}")
            return False
    
    async def list_exports(self, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """List all exports"""
        try:
            exports = list(self.active_exports.values())
            
            # Sort by creation date (newest first)
            exports.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
            
            # Apply pagination
            paginated_exports = exports[skip:skip + limit]
            
            # Remove sensitive file path info
            safe_exports = []
            for export in paginated_exports:
                safe_export = export.copy()
                safe_export.pop("file_path", None)  # Don't expose internal file paths
                safe_exports.append(safe_export)
            
            return safe_exports
            
        except Exception as e:
            logger.error(f"Failed to list exports: {e}")
            return []
    
    async def cleanup_old_exports(self, max_age_days: int = 7):
        """Clean up old export files"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
            
            exports_to_remove = []
            for export_id, export_info in self.active_exports.items():
                created_at = export_info.get("created_at")
                if created_at and created_at < cutoff_date:
                    exports_to_remove.append(export_id)
            
            cleaned_count = 0
            for export_id in exports_to_remove:
                if await self.delete_export(export_id):
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} old exports")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old exports: {e}")
            return 0
