import logging

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.generics import ListAPIView

from .models import Lead, LeadEvent, LeadFollowup, LeadFollowupRule
from .pagination import CommonPagination
from .serializers import (LeadEventSerializer, LeadFollowupRuleSerializer,
                          LeadFollowupSerializer, LeadSerializer)

logger = logging.getLogger('app')


@extend_schema(
    description='Retrieve a paginated list of leads.',
    parameters=[
        OpenApiParameter(
            name='limit',
            description='Maximum number of leads to return.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.INT,
        ),
        OpenApiParameter(
            name='offset',
            description='Number of records to skip before returning results.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.INT,
        ),
        OpenApiParameter(
            name='order_by',
            description='Lead field used for ordering.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            enum=tuple(field.name for field in Lead._meta.fields),
            default='updated_at',
        ),
        OpenApiParameter(
            name='order_dir',
            description='Ordering direction. Use "asc" or "desc" (default).',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            enum=['asc', 'desc'],
            default='desc',
        ),
    ],
    responses={200: LeadSerializer(many=True)},
)
class LeadListView(ListAPIView):
    serializer_class = LeadSerializer
    pagination_class = CommonPagination

    def get_queryset(self):
        default_order_field = 'updated_at'
        fields_for_order = tuple(field.name for field in Lead._meta.fields)
        params = self.request.query_params
        order_by = params.get('order_by', default_order_field)
        if order_by not in fields_for_order:
            logger.warning('Invalid order_by=%s supplied, falling back to %s', order_by, default_order_field)
            order_by = 'updated_at'

        order_dir = params.get('order_dir', 'desc').lower()
        if order_dir not in {'asc', 'desc'}:
            logger.debug('Invalid order_dir=%s supplied, using desc', order_dir)
            order_dir = 'desc'

        ordering = f'-{order_by}' if order_dir == 'desc' else order_by
        return Lead.objects.order_by(ordering)


@extend_schema(
    description='Retrieve a paginated list of lead followup.',
    parameters=[
        OpenApiParameter(
            name='limit',
            description='Maximum number of leads to return.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.INT,
        ),
        OpenApiParameter(
            name='offset',
            description='Number of records to skip before returning results.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.INT,
        ),
        OpenApiParameter(
            name='order_by',
            description='Lead field used for ordering.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            enum=tuple(field.name for field in LeadFollowup._meta.fields),
            default='created_at',
        ),
        OpenApiParameter(
            name='order_dir',
            description='Ordering direction. Use "asc" or "desc" (default).',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            enum=['asc', 'desc'],
            default='desc',
        ),
    ],
    responses={200: LeadFollowupSerializer(many=True)},
)
class LeadFollowupListView(ListAPIView):
    serializer_class = LeadFollowupSerializer
    pagination_class = CommonPagination

    def get_queryset(self):
        default_order_field = 'created_at'
        fields_for_order = tuple(field.name for field in LeadFollowup._meta.fields)
        params = self.request.query_params
        order_by = params.get('order_by', default_order_field)
        if order_by not in fields_for_order:
            logger.warning('Invalid order_by=%s supplied, falling back to %s', order_by, default_order_field)
            order_by = 'created_at'

        order_dir = params.get('order_dir', 'desc').lower()
        if order_dir not in {'asc', 'desc'}:
            logger.debug('Invalid order_dir=%s supplied, using desc', order_dir)
            order_dir = 'desc'

        ordering = f'-{order_by}' if order_dir == 'desc' else order_by
        return LeadFollowup.objects.order_by(ordering)


@extend_schema(
    description='Retrieve a paginated list of lead events.',
    parameters=[
        OpenApiParameter(
            name='limit',
            description='Maximum number of leads to return.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.INT,
        ),
        OpenApiParameter(
            name='offset',
            description='Number of records to skip before returning results.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.INT,
        ),
        OpenApiParameter(
            name='order_by',
            description='Lead field used for ordering.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            enum=tuple(field.name for field in LeadEvent._meta.fields),
            default='created_at',
        ),
        OpenApiParameter(
            name='order_dir',
            description='Ordering direction. Use "asc" or "desc" (default).',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            enum=['asc', 'desc'],
            default='desc',
        ),
    ],
    responses={200: LeadEventSerializer(many=True)},
)
class LeadEventListView(ListAPIView):
    serializer_class = LeadEventSerializer
    pagination_class = CommonPagination

    def get_queryset(self):
        default_order_field = 'created_at'
        fields_for_order = tuple(field.name for field in LeadEvent._meta.fields)
        params = self.request.query_params
        order_by = params.get('order_by', default_order_field)
        if order_by not in fields_for_order:
            logger.warning('Invalid order_by=%s supplied, falling back to %s', order_by, default_order_field)
            order_by = 'created_at'

        order_dir = params.get('order_dir', 'desc').lower()
        if order_dir not in {'asc', 'desc'}:
            logger.debug('Invalid order_dir=%s supplied, using desc', order_dir)
            order_dir = 'desc'

        ordering = f'-{order_by}' if order_dir == 'desc' else order_by
        return LeadEvent.objects.order_by(ordering)


@extend_schema(
    description='Retrieve a paginated list of lead followup rules.',
    parameters=[
        OpenApiParameter(
            name='limit',
            description='Maximum number of leads to return.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.INT,
        ),
        OpenApiParameter(
            name='offset',
            description='Number of records to skip before returning results.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.INT,
        ),
        OpenApiParameter(
            name='order_by',
            description='Lead field used for ordering.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            enum=tuple(field.name for field in LeadFollowupRule._meta.fields),
            default='status',
        ),
        OpenApiParameter(
            name='order_dir',
            description='Ordering direction. Use "asc" or "desc" (default).',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            enum=['asc', 'desc'],
            default='desc',
        ),
    ],
    responses={200: LeadFollowupRuleSerializer(many=True)},
)
class LeadFollowupRuleListView(ListAPIView):
    serializer_class = LeadFollowupRuleSerializer
    pagination_class = CommonPagination

    def get_queryset(self):
        default_order_field = 'status'
        fields_for_order = tuple(field.name for field in LeadFollowupRule._meta.fields)
        params = self.request.query_params
        order_by = params.get('order_by', default_order_field)
        if order_by not in fields_for_order:
            logger.warning('Invalid order_by=%s supplied, falling back to %s', order_by, default_order_field)
            order_by = 'status'

        order_dir = params.get('order_dir', 'desc').lower()
        if order_dir not in {'asc', 'desc'}:
            logger.debug('Invalid order_dir=%s supplied, using desc', order_dir)
            order_dir = 'desc'

        ordering = f'-{order_by}' if order_dir == 'desc' else order_by
        return LeadFollowupRule.objects.order_by(ordering)
