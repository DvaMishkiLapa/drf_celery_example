import logging

from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema)
from lead.models import Lead, LeadEvent, LeadFollowup, LeadFollowupRule
from lead.pagination import CommonPagination
from lead.serializers import (LeadEventSerializer, LeadFollowupRuleSerializer,
                              LeadFollowupSerializer, LeadSerializer,
                              NewLeadStatusValidator)
from rest_framework import status as http_status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response

logger = logging.getLogger('app')


@extend_schema(
    description='Retrieve a paginated list of leads.',
    parameters=[
        OpenApiParameter(
            name='limit',
            description='Maximum number of leads to return.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.INT
        ),
        OpenApiParameter(
            name='offset',
            description='Number of records to skip before returning results.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.INT
        ),
        OpenApiParameter(
            name='order_by',
            description='Lead field used for ordering.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            enum=tuple(field.name for field in Lead._meta.fields),
            default='updated_at'
        ),
        OpenApiParameter(
            name='order_dir',
            description='Ordering direction. Use "asc" or "desc" (default).',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            enum=['asc', 'desc'],
            default='desc'
        )
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
            type=OpenApiTypes.INT
        ),
        OpenApiParameter(
            name='offset',
            description='Number of records to skip before returning results.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.INT
        ),
        OpenApiParameter(
            name='order_by',
            description='Lead field used for ordering.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            enum=tuple(field.name for field in LeadFollowup._meta.fields),
            default='created_at'
        ),
        OpenApiParameter(
            name='order_dir',
            description='Ordering direction. Use "asc" or "desc" (default).',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            enum=['asc', 'desc'],
            default='desc'
        )
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
            type=OpenApiTypes.INT
        ),
        OpenApiParameter(
            name='offset',
            description='Number of records to skip before returning results.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.INT
        ),
        OpenApiParameter(
            name='order_by',
            description='Lead field used for ordering.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            enum=tuple(field.name for field in LeadEvent._meta.fields),
            default='created_at'
        ),
        OpenApiParameter(
            name='order_dir',
            description='Ordering direction. Use "asc" or "desc" (default).',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            enum=['asc', 'desc'],
            default='desc'
        )
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
            type=OpenApiTypes.INT
        ),
        OpenApiParameter(
            name='offset',
            description='Number of records to skip before returning results.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.INT
        ),
        OpenApiParameter(
            name='order_by',
            description='Lead field used for ordering.',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            enum=tuple(field.name for field in LeadFollowupRule._meta.fields),
            default='status'
        ),
        OpenApiParameter(
            name='order_dir',
            description='Ordering direction. Use "asc" or "desc" (default).',
            required=False,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            enum=['asc', 'desc'],
            default='desc'
        )
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


@extend_schema(
    description='Updates the status of a Lead and makes changes to its status history.',
    request={'application/json': NewLeadStatusValidator},
    responses={200: LeadEventSerializer()},
    examples=[
        OpenApiExample(
            name='ex1',
            summary='Set status SUBMITTED',
            value={
                'lead_id': 1,
                'status': 'submitted'
            },
            media_type='application/json'
        )
    ]
)
class LeadEventCreateView(CreateAPIView):
    serializer_class = NewLeadStatusValidator

    def create(self, request, *args, **kwargs):
        in_ser = self.get_serializer(data=request.data)
        in_ser.is_valid(raise_exception=True)

        lead_id = in_ser.validated_data['lead_id']
        new_status = in_ser.validated_data['status']

        with transaction.atomic():
            lead = Lead.objects.select_for_update().get(pk=lead_id)
            if lead.status != new_status:
                lead.status = new_status
                lead.save(update_fields=['status', 'updated_at'])

            event = LeadEvent.objects.create(
                lead=lead,
                status=new_status
            )

        out_ser = LeadEventSerializer(event, context={'request': request})
        return Response(out_ser.data, status=http_status.HTTP_201_CREATED)
