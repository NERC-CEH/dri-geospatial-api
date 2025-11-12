from fastapi import APIRouter

router = APIRouter(tags=["Healthcheck"])


@router.get("/healthcheck/")
def healthcheck() -> dict[str, str]:
    """
    \f
    Test endpoint to check the API is running.

    Returns:
        A JSON containing the key status with value ok.
    """
    return {"status": "ok"}
