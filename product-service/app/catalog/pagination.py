from rest_framework.pagination import CursorPagination
from django.conf import settings

class ProductCursorPagination(CursorPagination):
    page_size = 10
    ordering = "-created_at"


class CategoryCursorPagination(CursorPagination):
    page_size = 10
    ordering = "-created_at"

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        
        # If your links are still missing the port, you can force-replace them here.
        # This is a fallback if USE_X_FORWARDED_PORT = True doesn't work.
        if settings.DEBUG:
            next_link = response.data.get('next')
            prev_link = response.data.get('previous')
            
            if next_link and 'localhost:8000' not in next_link:
                response.data['next'] = next_link.replace('localhost', 'localhost:8000')
            if prev_link and 'localhost:8000' not in prev_link:
                response.data['previous'] = prev_link.replace('localhost', 'localhost:8000')
                
        return response