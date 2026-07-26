"""Orchestrator tools for managing website workflows."""

from __future__ import annotations

from uuid import UUID

from app.config import get_settings
from app.database import website_db
from app.llm.infra.types import ToolError, ToolResult
from app.llm.orchestrator_agent.tools._base import get_run_context, register_tool
from app.models.workflow import WorkflowDeliveryTarget
from app.services import workflow_service
from app.utils.db_session import get_async_session_maker


def _error(code: str, message: str) -> ToolResult:
    return ToolResult(
        status="error",
        error=ToolError(
            code=code,
            message=message,
            retryable=False,
            handled_by="service",
        ),
    )


def _parse_delivery(delivery: str) -> WorkflowDeliveryTarget | ToolResult:
    """The delivery string as an enum, or an error ToolResult for the caller to return."""
    try:
        return WorkflowDeliveryTarget(delivery)
    except ValueError:
        return _error(
            "invalid_delivery",
            "delivery must be one of: thread, default_channel, none.",
        )


def _serialize_workflow(workflow) -> dict:
    return {
        "id": str(workflow.id),
        "team_id": str(workflow.team_id),
        "website_id": str(workflow.website_id) if workflow.website_id else None,
        "cron_expression": workflow.cron_expression,
        "prompt": workflow.prompt,
        "title": workflow.title,
        "delivery": workflow.delivery_target,
        "enabled": workflow.enabled,
        "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
        "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
    }


async def _require_context() -> tuple[UUID, str, str, UUID, UUID | None] | ToolResult:
    """Resolve the workflow's owning team from the website the user is editing.

    Workflows are team-owned, but the conversational surface is a website chat,
    so the team is derived from the active website. Returns
    ``(team_id, creator_id, creator_email, website_id, source_thread_id)``.
    """
    run_context = get_run_context()
    website_id = run_context.get("website_id")
    creator_id = run_context.get("creator_id")
    creator_email = run_context.get("creator_email")
    if not website_id or not creator_id or not creator_email:
        return _error("missing_context", "Missing website or user context for workflow tool.")

    website_uuid = UUID(str(website_id))
    source_thread_id = run_context.get("thread_id")
    session_maker = get_async_session_maker(get_settings())
    async with session_maker() as db_session:
        team_id = await website_db.get_team_id_for_website(db_session, website_uuid)
    if team_id is None:
        return _error("team_not_found", "Could not resolve the team for the current website.")

    return (
        team_id,
        str(creator_id),
        str(creator_email),
        website_uuid,
        UUID(str(source_thread_id)) if source_thread_id else None,
    )


@register_tool
async def create_workflow(
    cron_expression: str,
    prompt: str,
    title: str,
    delivery: str = WorkflowDeliveryTarget.DEFAULT_CHANNEL,
) -> ToolResult:
    """Create a UTC cron workflow for recurring team work.

    Args:
        cron_expression: Five-field UTC cron expression.
        prompt: The exact instruction sent to the team CMO at trigger time.
        title: Short display name (at most 6 words) shown in the workflows UI.
        delivery: Where a fired run reports its result. "default_channel"
            (default) posts to the team's home Slack channel; "thread" replies in
            this conversation; "none" reports only to the Tasks UI.
    """
    # Only creation is recursion-guarded: a scheduled run spawning new workflows
    # is the unbounded-fan-out risk. list/update/delete stay allowed so a workflow
    # can disable or delete itself when its job is done.
    if get_run_context().get("source_channel") == "scheduler":
        return _error(
            "scheduler_recursion_blocked",
            "Scheduled runs cannot create workflows.",
        )
    delivery_target = _parse_delivery(delivery)
    if not isinstance(delivery_target, WorkflowDeliveryTarget):
        return delivery_target
    context = await _require_context()
    if not isinstance(context, tuple):
        return context
    team_id, creator_id, creator_email, website_id, source_thread_id = context
    session_maker = get_async_session_maker(get_settings())
    async with session_maker() as db_session:
        try:
            workflow = await workflow_service.create_workflow(
                db_session,
                team_id=team_id,
                creator_id=creator_id,
                creator_email=creator_email,
                website_id=website_id,
                source_thread_id=source_thread_id,
                cron_expression=cron_expression,
                prompt=prompt,
                title=title,
                delivery_target=delivery_target,
            )
            await db_session.refresh(workflow)
            serialized = _serialize_workflow(workflow)
            await db_session.commit()
        except ValueError as e:
            await db_session.rollback()
            return _error("invalid_workflow", str(e))

        return ToolResult(status="success", result={"workflow": serialized})


@register_tool
async def list_workflows(include_disabled: bool = False) -> ToolResult:
    """List recurring workflows for the current team.

    Args:
        include_disabled: Include disabled workflows when true.
    """
    context = await _require_context()
    if not isinstance(context, tuple):
        return context
    team_id, _creator_id, _creator_email, _website_id, _source_thread_id = context
    session_maker = get_async_session_maker(get_settings())
    async with session_maker() as db_session:
        workflows = await workflow_service.list_workflows(
            db_session,
            team_id=team_id,
            include_disabled=include_disabled,
        )
        return ToolResult(
            status="success",
            result={"workflows": [_serialize_workflow(workflow) for workflow in workflows]},
        )


@register_tool
async def update_workflow(
    workflow_id: str,
    cron_expression: str | None = None,
    prompt: str | None = None,
    enabled: bool | None = None,
    delivery: str | None = None,
) -> ToolResult:
    """Update a recurring workflow for the current team.

    Args:
        workflow_id: Workflow UUID to update.
        cron_expression: Optional replacement five-field UTC cron expression.
        prompt: Optional replacement prompt.
        enabled: Optional enabled/disabled state.
        delivery: Optional new delivery target ("thread" | "default_channel" |
            "none"). "thread" requires the workflow to have a source thread.
    """
    delivery_target: WorkflowDeliveryTarget | None = None
    if delivery is not None:
        parsed = _parse_delivery(delivery)
        if not isinstance(parsed, WorkflowDeliveryTarget):
            return parsed
        delivery_target = parsed
    context = await _require_context()
    if not isinstance(context, tuple):
        return context
    team_id, _creator_id, _creator_email, _website_id, _source_thread_id = context
    try:
        workflow_uuid = UUID(workflow_id)
    except ValueError:
        return _error("invalid_workflow_id", "workflow_id must be a UUID.")

    session_maker = get_async_session_maker(get_settings())
    async with session_maker() as db_session:
        try:
            workflow = await workflow_service.update_workflow(
                db_session,
                workflow_id=workflow_uuid,
                team_id=team_id,
                cron_expression=cron_expression,
                prompt=prompt,
                enabled=enabled,
                delivery_target=delivery_target,
            )
            await db_session.refresh(workflow)
            serialized = _serialize_workflow(workflow)
            await db_session.commit()
        except ValueError as e:
            await db_session.rollback()
            return _error("invalid_workflow", str(e))

        return ToolResult(status="success", result={"workflow": serialized})


@register_tool
async def delete_workflow(workflow_id: str) -> ToolResult:
    """Soft-delete a recurring workflow for the current team.

    Args:
        workflow_id: Workflow UUID to delete.
    """
    context = await _require_context()
    if not isinstance(context, tuple):
        return context
    team_id, _creator_id, _creator_email, _website_id, _source_thread_id = context
    try:
        workflow_uuid = UUID(workflow_id)
    except ValueError:
        return _error("invalid_workflow_id", "workflow_id must be a UUID.")

    session_maker = get_async_session_maker(get_settings())
    async with session_maker() as db_session:
        try:
            workflow = await workflow_service.delete_workflow(
                db_session,
                workflow_id=workflow_uuid,
                team_id=team_id,
            )
            await db_session.refresh(workflow)
            serialized = _serialize_workflow(workflow)
            await db_session.commit()
        except ValueError as e:
            await db_session.rollback()
            return _error("invalid_workflow", str(e))

        return ToolResult(status="success", result={"workflow": serialized})
