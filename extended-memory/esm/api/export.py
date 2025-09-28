"""Export API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
import logging
from pathlib import Path

from esm.schemas import ExportRequest, ExportResponse
from esm.services.export_service import ExportService

router = APIRouter()
logger = logging.getLogger(__name__)


def get_export_service() -> ExportService:
    """Get export service dependency"""
    return ExportService()


@router.post("/", response_model=ExportResponse)
async def create_export(
    export_request: ExportRequest,
    background_tasks: BackgroundTasks,
    export_service: ExportService = Depends(get_export_service)
):
    """Create a new export job"""
    try:
        export_info = await export_service.create_export(export_request)
        
        # Add background task to generate the export file
        background_tasks.add_task(
            export_service.generate_export_file,
            export_info["export_id"],
            export_request
        )
        
        logger.info(f"Created export job {export_info['export_id']}")
        return ExportResponse(**export_info)
    except Exception as e:
        logger.error(f"Failed to create export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create export"
        )


@router.get("/{export_id}/status")
async def get_export_status(
    export_id: str,
    export_service: ExportService = Depends(get_export_service)
):
    """Get export job status"""
    try:
        status_info = await export_service.get_export_status(export_id)
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Export with ID {export_id} not found"
            )
        return status_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get export status {export_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get export status"
        )


@router.get("/{export_id}/download")
async def download_export(
    export_id: str,
    export_service: ExportService = Depends(get_export_service)
):
    """Download export file"""
    try:
        file_path = await export_service.get_export_file_path(export_id)
        if not file_path or not Path(file_path).exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export file not found or not ready"
            )
        
        # Get file info for proper response
        export_info = await export_service.get_export_status(export_id)
        filename = f"esm_export_{export_id}.{export_info['format']}"
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download export {export_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download export"
        )


@router.delete("/{export_id}")
async def delete_export(
    export_id: str,
    export_service: ExportService = Depends(get_export_service)
):
    """Delete export and its file"""
    try:
        success = await export_service.delete_export(export_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Export with ID {export_id} not found"
            )
        
        logger.info(f"Deleted export {export_id}")
        return {"message": "Export deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete export {export_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete export"
        )


@router.get("/")
async def list_exports(
    skip: int = 0,
    limit: int = 50,
    export_service: ExportService = Depends(get_export_service)
):
    """List all exports"""
    try:
        exports = await export_service.list_exports(skip=skip, limit=limit)
        return {"exports": exports}
    except Exception as e:
        logger.error(f"Failed to list exports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list exports"
        )


@router.post("/quick-json")
async def quick_json_export(
    assistant_id: int = None,
    export_service: ExportService = Depends(get_export_service)
):
    """Quick JSON export for immediate download"""
    try:
        export_request = ExportRequest(
            assistant_id=assistant_id,
            format="json",
            include_shared=True
        )
        
        # Generate export immediately (not as background task)
        file_path = await export_service.generate_export_immediately(export_request)
        
        filename = f"esm_quick_export_{assistant_id or 'all'}.json"
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/json"
        )
    except Exception as e:
        logger.error(f"Failed to create quick export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create quick export"
        )