from typing import Any, List

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class CommonPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100
    limit_query_param = 'limit'
    offset_query_param = 'offset'

    def get_paginated_response(self, data):
        return Response({
            'count': self.count,
            'results': data
        })


def limit_offset_pagination(items: List[Any], offset: int, limit: int = 10, max_limit: int = 100) -> List[Any]:
    if limit > max_limit:
        limit = max_limit
    end = offset + limit
    return items[offset:end]
