import logging

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import (OpenApiParameter, OpenApiResponse,
                                   extend_schema)
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response

logger = logging.getLogger('app')
