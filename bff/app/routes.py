from __future__ import annotations

from dataclasses import dataclass

from .config import get_settings


@dataclass(frozen=True)
class ServiceRoute:
    frontend_prefix: str
    service_base_url: str


def get_service_routes() -> dict[str, ServiceRoute]:
    settings = get_settings()
    return {
        "service-a": ServiceRoute(
            frontend_prefix="/api/service-a",
            service_base_url=settings.service_a_base_url,
        ),
        "service-b": ServiceRoute(
            frontend_prefix="/api/service-b",
            service_base_url=settings.service_b_base_url,
        ),
    }
