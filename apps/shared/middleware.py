import time, uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from .logging import logger, request_log_fields

REQUEST_ID_HEADER = "X-Request-ID"

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = rid
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error("unhandled_exception", request_id=rid, error=str(exc))
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": rid},
            )
        finally:
            dur_ms = (time.perf_counter() - start) * 1000
            logger.info(**request_log_fields(request.method, request.url.path, getattr(locals().get("response", None), "status_code", 500), dur_ms, rid))
            # Record Prometheus metrics if available
            try:
                from apps.guard_api.metrics import observe_latency
                observe_latency(request.url.path, request.method, dur_ms)
            except (ImportError, ModuleNotFoundError):
                # Prometheus metrics not available, skip
                pass
        response.headers[REQUEST_ID_HEADER] = rid
        return response

def add_health_routes(app):
    @app.get("/healthz", tags=["system"])
    async def healthz():
        return {"ok": True}

    @app.get("/readyz", tags=["system"])
    async def readyz():
        # extend with Temporal/GitHub checks if desired
        return {"ready": True}