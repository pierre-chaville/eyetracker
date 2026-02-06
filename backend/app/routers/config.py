from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import ConfigService
from app.dependencies import get_config_service
from app.schemas import ConfigModel, ConfigResponse
from app.utils.exceptions import ConfigSaveError, ConfigValidationError

router = APIRouter(tags=["setup"])


@router.get("/api/config", response_model=ConfigResponse)
async def get_config(
    service: ConfigService = Depends(get_config_service),
) -> ConfigResponse:
    """Get current configuration."""
    return service.get_config()


@router.put("/api/config", response_model=ConfigResponse)
async def update_config(
    config: ConfigModel,
    service: ConfigService = Depends(get_config_service),
) -> ConfigResponse:
    """Update configuration."""
    try:
        return service.update_config(config)
    except ConfigValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except ConfigSaveError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.detail,
        ) from exc
