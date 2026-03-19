import logging
import time
import json

logger = logging.getLogger(__name__)


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time

        log = {
            "event": "http_request",
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration": round(duration, 3),
        }

        logger.info(json.dumps(log))

        return response


class ErrorLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as e:
            logger.error(
                json.dumps(
                    {"event": "unhandled_error", "path": request.path, "error": str(e)}
                )
            )
            raise
