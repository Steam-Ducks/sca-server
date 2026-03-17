from django.http import JsonResponse
import logging
logger = logging.getLogger(__name__)

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health_check(request):
    return Response({"status": "ok", "version": "1.0.0"})


def test_log(request):
    logger.info("test endpoint accessed")
    return JsonResponse({"status": "ok"})