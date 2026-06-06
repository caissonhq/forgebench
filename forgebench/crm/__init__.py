"""ForgeBench customer relationship helpers — local pipeline and onboarding."""

from forgebench.crm.onboarding import build_paid_customer_checklist, format_welcome_sequence
from forgebench.crm.pipeline import PipelineStage, load_pipeline, record_subscription_event

__all__ = [
    "PipelineStage",
    "load_pipeline",
    "record_subscription_event",
    "build_paid_customer_checklist",
    "format_welcome_sequence",
]