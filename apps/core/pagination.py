import math

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        page_size = self.get_page_size(self.request) or self.page_size
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

        return Response({
            'data': data,
            'pagination': {
                'page': self.page.number,
                'limit': page_size,
                'totalItems': total_items,
                'totalPages': total_pages,
                'hasNext': self.page.has_next(),
                'hasPrev': self.page.has_previous(),
            }
        })

    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'data': schema,
                'pagination': {
                    'type': 'object',
                    'properties': {
                        'page': {'type': 'integer'},
                        'limit': {'type': 'integer'},
                        'totalItems': {'type': 'integer'},
                        'totalPages': {'type': 'integer'},
                        'hasNext': {'type': 'boolean'},
                        'hasPrev': {'type': 'boolean'},
                    }
                }
            }
        }
