"""Design generation tool for the orchestrator."""

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.constants import AGENT_COMPLETED, AGENT_TRIGGERED
from app.llm.coding import website_create
from app.llm.infra.types import ToolError, ToolResult
from app.llm.orchestrator_agent.tools._base import (
    get_run_context,
    register_tool,
)
from app.services import analytics_service

logger = logging.getLogger(__name__)


class DesignSpec(BaseModel):
    """Specification for generating a single design."""

    user_requirements: str = Field(
        description="The user's requirements for this specific design. For initial generation, include base requirements plus a per-design style hint phrased for this one design ('Use a bold editorial style with …'). Exclude platform-workflow directives (how many designs to create, comparison requests, 'don't ask questions') — this call itself fulfils them, and echoed text gets built into the site. For remixes, include only the change requests that apply to this design."
    )
    remix: bool = Field(
        default=False,
        description="False to create a brand new design. True to edit the existing design with the changes in user_requirements.",
    )
    contexts: list[str] = Field(
        default_factory=list,
        description='References to other designs to use as context. Values: "PROTOTYPE_1", "PROTOTYPE_2", "PROTOTYPE_3".',
    )


@register_tool
async def generate_designs(
    designs: list[Optional[DesignSpec]],
) -> ToolResult:
    """
    Generate or regenerate website designs for user comparison.
    Creates up to 3 design options in parallel.

    The designs argument is a list of exactly 3 items (one per design slot).
    Each item is either a DesignSpec object or null:
    - DesignSpec: generate/regenerate that design
    - null: keep that design unchanged

    For the FIRST call after discovery, pass 3 DesignSpec objects all with
    remix=false. Each should have user_requirements that include the shared
    base requirements PLUS a per-design variation hint (e.g. style direction,
    layout preference, visual mood) to produce meaningfully different designs.
    Never copy platform-workflow directives into user_requirements — requests
    to create or compare N designs/variations/directions are fulfilled by this
    call itself; each builder sees only its own spec and will otherwise render
    that text as site content (e.g. a literal "design directions" page).

    For subsequent calls (edits), each DesignSpec should include only the
    change requests relevant to THAT specific design (not a shared message).
    Pass null for designs that should remain unchanged.

    Args:
        designs: List of exactly 3 items. Each is a DesignSpec or null.
            Example for initial generation (per-design variation):
            [
                {"user_requirements": "Build a website for [Business Name], a [business type] in [City, State]. Address: [street address]. Phone: [phone number]. Hours: [operating hours]. Include testimonials from [Name] ('[quote]') and [Name] ('[quote]'). Feature [product/service names and descriptions]. Use a clean modern layout with [style descriptors].", "remix": false, "contexts": []},
                {"user_requirements": "Build a website for [Business Name], a [business type] in [City, State]. Address: [street address]. Phone: [phone number]. Hours: [operating hours]. Include testimonials from [Name] ('[quote]') and [Name] ('[quote]'). Feature [product/service names and descriptions]. Use a bold editorial style with [style descriptors].", "remix": false, "contexts": []},
                {"user_requirements": "Build a website for [Business Name], a [business type] in [City, State]. Address: [street address]. Phone: [phone number]. Hours: [operating hours]. Include testimonials from [Name] ('[quote]') and [Name] ('[quote]'). Feature [product/service names and descriptions]. Use a warm photographic style with [style descriptors].", "remix": false, "contexts": []}
            ]
            Example for editing design 2 only:
            [
                null,
                {"user_requirements": "Make the hero section darker", "remix": true, "contexts": []},
                null
            ]

    Returns:
        Summary of generation results
    """
    run_context = get_run_context()

    website_id = run_context["website_id"]
    thread_id = run_context["thread_id"]
    creator_id = run_context["creator_id"]
    creator_email = run_context.get("creator_email", "")

    try:
        analytics_service.track_event(
            user_id=creator_id,
            event=AGENT_TRIGGERED,
            properties={
                "agent_name": "generate_designs",
                # TODO(V2-3857): drop "application_id" once PostHog analytics queries migrate to website_id
                "application_id": website_id,
                "website_id": website_id,
                "thread_id": thread_id,
                "user_email": creator_email,
            },
        )
    except Exception as track_error:
        logger.warning(f"Failed to track {AGENT_TRIGGERED} event: {track_error!r}")

    # Convert DesignSpec objects to dicts for the service
    design_dicts = [d.model_dump() if d is not None else None for d in designs]

    result = await website_create.run(
        designs=design_dicts,
        website_id=website_id,
        thread_id=thread_id,
        creator_id=creator_id,
        creator_email=creator_email,
        message_id=run_context.get("message_id"),
    )

    try:
        analytics_service.track_event(
            user_id=creator_id,
            event=AGENT_COMPLETED,
            properties={
                "agent_name": "generate_designs",
                "status": result.get("status", "success"),
                # TODO(V2-3857): drop "application_id" once PostHog analytics queries migrate to website_id
                "application_id": website_id,
                "website_id": website_id,
                "thread_id": thread_id,
                "user_email": creator_email,
            },
        )
    except Exception as track_error:
        logger.warning(f"Failed to track {AGENT_COMPLETED} event: {track_error!r}")

    status = result.get("status", "success")
    if status == "error":
        return ToolResult(
            status="error",
            error=ToolError(
                code="design_generation_failed",
                message=result.get("message", "Design generation failed"),
                retryable=False,
                handled_by="service",
            ),
        )
    result_without_status: dict[str, Any] = {k: v for k, v in result.items() if k != "status"}
    if status == "partial":
        return ToolResult(
            status="partial",
            result=result_without_status,
            warnings=[result.get("message", "Some design generation tasks failed")],
        )
    return ToolResult(
        status="success",
        result=result_without_status,
    )
