from fastapi import APIRouter

public_router = APIRouter(tags=["Public", "Healthcheck"])


@public_router.get("/healthcheck/")
def healthcheck() -> dict[str, str]:
    """
    \f
    Test endpoint to check the API is running.

    Returns:
        A JSON containing the key status with value ok.
    """
    return {"status": "ok"}
