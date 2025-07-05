"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from urllib.parse import urljoin

class AdminUserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        total_pages = self.page.paginator.num_pages
        current_page = self.page.number

        return Response({
            'links': {
                'first': self.build_absolute_uri(self.get_page_link(1)),
                'previous': self.build_absolute_uri(self.get_previous_link()),
                'next': self.build_absolute_uri(self.get_next_link()),
                'last': self.build_absolute_uri(self.get_page_link(total_pages)),
            },
            'meta': {
                'current_page': current_page,
                'page_size': self.page.paginator.per_page,
                'total_pages': total_pages,
                'total_items': self.page.paginator.count,
            },
            'results': data
        })

    def build_absolute_uri(self, url):
        if url is None:
            return None

        # Dynamically determine the base URL from the request
        request = self.request
        scheme = request.scheme  # 'http' or 'https'
        host = request.get_host()  # '127.0.0.1:8000' or 'tracemapr.com'

        # Custom logic: Add '/backend' for production domain
        if 'tracemapr.com' in host:
            base_url = f"{scheme}://{host}/backend"
        else:
            base_url = f"{scheme}://{host}"

        # Extract path after '/api/'
        path = url.split('/api/', 1)[-1]
        return urljoin(f"{base_url}/api/", path)

    def get_page_link(self, page_number):
        if page_number < 1 or page_number > self.page.paginator.num_pages:
            return None
        request = self.request
        query_params = request.query_params.copy()
        query_params[self.page_query_param] = page_number
        return f'{request.path}?{query_params.urlencode()}'
