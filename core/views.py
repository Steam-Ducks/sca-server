import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


# Healthcheck (safe)
@api_view(["GET"])
def health_check(request):
    return Response({"status": "ok"}, status=status.HTTP_200_OK)


# Simple log test (safe)
@require_GET
def test_log(request):
    logger.info("test endpoint accessed")
    return JsonResponse({"status": "ok"})


# Receives logs from the frontend
@csrf_exempt
@require_POST
def receive_log(request):
    try:
        data = json.loads(request.body or "{}")

        logger.info("frontend_log", extra={"custom_data": data})

        return JsonResponse({"status": "ok"})

    except Exception as e:
        logger.error("receive_log_error", extra={"error": str(e)})
        return JsonResponse({"error": str(e)}, status=500)


# Receives metrics from the frontend
@csrf_exempt
@require_POST
def receive_metric(request):
    try:
        data = json.loads(request.body or "{}")

        logger.info("frontend_metric", extra={"custom_data": data})

        return JsonResponse({"status": "ok"})

    except Exception as e:
        logger.error("receive_metric_error", extra={"error": str(e)})
        return JsonResponse({"error": str(e)}, status=500)
