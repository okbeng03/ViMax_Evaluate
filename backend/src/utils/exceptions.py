"""Custom exception classes and error handling."""

from typing import Optional, Any


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[dict] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppException):
    """Validation error exception."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class TaskNotFoundError(AppException):
    """Task not found exception."""

    def __init__(self, task_id: str):
        super().__init__(
            message=f"Task not found: {task_id}",
            code="TASK_NOT_FOUND",
            details={"task_id": task_id},
        )


class ProjectNotFoundError(AppException):
    """Project not found exception."""

    def __init__(self, project_id: str):
        super().__init__(
            message=f"Project not found: {project_id}",
            code="PROJECT_NOT_FOUND",
            details={"project_id": project_id},
        )


class TaskNotCompletedError(AppException):
    """Task not completed exception."""

    def __init__(self, task_id: str, status: str):
        super().__init__(
            message=f"Task not completed: {task_id} (status: {status})",
            code="TASK_NOT_COMPLETED",
            details={"task_id": task_id, "status": status},
        )


class ImageLoadError(AppException):
    """Image load error exception."""

    def __init__(self, message: str, url: Optional[str] = None):
        super().__init__(
            message=message,
            code="IMAGE_LOAD_FAILED",
            details={"url": url} if url else {},
        )


class ImageFormatError(AppException):
    """Image format not supported exception."""

    SUPPORTED_FORMATS = ["PNG", "JPG", "JPEG", "WebP"]

    def __init__(self, received_format: str):
        super().__init__(
            message=f"Unsupported image format: {received_format}. Supported: {', '.join(self.SUPPORTED_FORMATS)}",
            code="IMAGE_FORMAT_UNSUPPORTED",
            details={"received_format": received_format},
        )


class ModelLoadError(AppException):
    """Model load error exception."""

    def __init__(self, model_name: str, message: str):
        super().__init__(
            message=f"Failed to load model {model_name}: {message}",
            code="MODEL_LOAD_FAILED",
            details={"model_name": model_name},
        )


class ComfyUIError(AppException):
    """ComfyUI API error exception."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(
            message=message,
            code="COMFYUI_ERROR",
            details={"status_code": status_code} if status_code else {},
        )


class LLMError(AppException):
    """LLM API error exception."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=f"LLM error: {message}",
            code="LLM_ERROR",
            details=details or {},
        )
