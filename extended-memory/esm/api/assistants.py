"""Assistant Management API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from esm.database import get_db
from esm.schemas import AssistantCreate, AssistantUpdate, AssistantResponse
from esm.services.assistant_service import AssistantService
from esm.api.dependencies import get_assistant_by_id
from esm.models import Assistant

router = APIRouter()
logger = logging.getLogger(__name__)


def get_assistant_service(db: Session = Depends(get_db)) -> AssistantService:
    """Get assistant service dependency"""
    return AssistantService(db)


@router.get("/", response_model=List[AssistantResponse])
async def list_assistants(
    assistant_service: AssistantService = Depends(get_assistant_service)
):
    """List all assistants"""
    try:
        assistants = await assistant_service.list_assistants()
        return assistants
    except Exception as e:
        logger.error(f"Failed to list assistants: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve assistants"
        )


@router.post("/", response_model=AssistantResponse, status_code=status.HTTP_201_CREATED)
async def create_assistant(
    assistant_data: AssistantCreate,
    assistant_service: AssistantService = Depends(get_assistant_service)
):
    """Create a new assistant"""
    try:
        assistant = await assistant_service.create_assistant(assistant_data)
        logger.info(f"Created assistant: {assistant.name}")
        return assistant
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create assistant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create assistant"
        )


@router.get("/{assistant_id}", response_model=AssistantResponse)
async def get_assistant(
    assistant: Assistant = Depends(get_assistant_by_id)
):
    """Get assistant by ID"""
    return assistant


@router.put("/{assistant_id}", response_model=AssistantResponse)
async def update_assistant(
    assistant_id: int,
    assistant_data: AssistantUpdate,
    assistant_service: AssistantService = Depends(get_assistant_service)
):
    """Update an assistant"""
    try:
        assistant = await assistant_service.update_assistant(assistant_id, assistant_data)
        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assistant with ID {assistant_id} not found"
            )
        logger.info(f"Updated assistant {assistant_id}")
        return assistant
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update assistant {assistant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update assistant"
        )


@router.delete("/{assistant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assistant(
    assistant_id: int,
    assistant_service: AssistantService = Depends(get_assistant_service)
):
    """Delete an assistant"""
    try:
        success = await assistant_service.delete_assistant(assistant_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assistant with ID {assistant_id} not found"
            )
        logger.info(f"Deleted assistant {assistant_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete assistant {assistant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete assistant"
        )


@router.get("/{assistant_id}/memories/count")
async def get_memory_count(
    assistant_id: int,
    assistant_service: AssistantService = Depends(get_assistant_service)
):
    """Get memory count for an assistant"""
    try:
        count = await assistant_service.get_memory_count(assistant_id)
        return {"assistant_id": assistant_id, "memory_count": count}
    except Exception as e:
        logger.error(f"Failed to get memory count for assistant {assistant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get memory count"
        )


@router.post("/{assistant_id}/activate")
async def activate_assistant(
    assistant_id: int,
    assistant_service: AssistantService = Depends(get_assistant_service)
):
    """Activate an assistant"""
    try:
        assistant = await assistant_service.set_assistant_status(assistant_id, True)
        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assistant with ID {assistant_id} not found"
            )
        return {"message": f"Assistant {assistant_id} activated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate assistant {assistant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate assistant"
        )


@router.post("/{assistant_id}/deactivate")
async def deactivate_assistant(
    assistant_id: int,
    assistant_service: AssistantService = Depends(get_assistant_service)
):
    """Deactivate an assistant"""
    try:
        assistant = await assistant_service.set_assistant_status(assistant_id, False)
        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assistant with ID {assistant_id} not found"
            )
        return {"message": f"Assistant {assistant_id} deactivated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate assistant {assistant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate assistant"
        )