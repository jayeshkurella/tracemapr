"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from urllib.parse import urljoin


# pagination for the Approval of cases by Admin

class StatusPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        total_pages = self.page.paginator.num_pages
        current_page = self.page.number

        return Response(
            {
                "links": {
                    "first": self._build_absolute_uri(self._get_page_link(1)),
                    "previous": self._build_absolute_uri(self.get_previous_link()),
                    "next": self._build_absolute_uri(self.get_next_link()),
                    "last": self._build_absolute_uri(self._get_page_link(total_pages)),
                },
                "meta": {
                    "current_page": current_page,
                    "page_size": self.page.paginator.per_page,
                    "total_pages": total_pages,
                    "total_items": self.page.paginator.count,
                },
                "results": data,
            }
        )


    def _build_absolute_uri(self, url: str | None) -> str | None:
        """
        • Turn DRF’s relative/absolute pagination URLs into the canonical form your
          front‑end expects.
        • For production (`tracemapr.com`) prepend `/backend`.
        """
        if url is None:
            return None

        request = self.request
        scheme = request.scheme  # http / https
        host = request.get_host()

        base_url = f"{scheme}://{host}/backend" if "tracemapr.com" in host else f"{scheme}://{host}"

        path_after_api = url.split("/api/", 1)[-1]
        return urljoin(f"{base_url}/api/", path_after_api)

    def _get_page_link(self, page_number: int) -> str | None:
        """
        Return a relative link (?page=N…) for an arbitrary page number so that
        _build_absolute_uri can convert it to the final absolute URL.
        """
        if not (1 <= page_number <= self.page.paginator.num_pages):
            return None

        request = self.request
        query_params = request.query_params.copy()
        query_params[self.page_query_param] = page_number
        return f"{request.path}?{query_params.urlencode()}"
