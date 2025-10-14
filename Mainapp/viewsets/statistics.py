from datetime import date, timedelta
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from ..models import Person


class PersonStatisticsAPIView(APIView):
    permission_classes = [AllowAny]  # Change to IsAuthenticated if needed

    def get(self, request):
        today = date.today()
        first_day_this_month = today.replace(day=1)

        # Last month date range
        last_month_end = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_month_end.replace(day=1)

        # =========================
        # BASIC COUNTS (CURRENT MONTH)
        # =========================
        total_cases = Person.objects.filter(_is_deleted=False).count()
        resolved_cases = Person.objects.filter(case_status='resolved', _is_deleted=False).count()
        active_cases = Person.objects.filter(is_active=True, _is_deleted=False).count()
        resolution_rate = (resolved_cases / total_cases * 100) if total_cases > 0 else 0

        # =========================
        # LAST MONTH COUNTS
        # =========================
        last_month_cases = Person.objects.filter(
            _is_deleted=False,
            reported_date__range=[first_day_last_month, last_month_end]
        )

        total_cases_last = last_month_cases.count()
        resolved_cases_last = last_month_cases.filter(case_status='resolved').count()
        active_cases_last = last_month_cases.filter(is_active=True).count()
        resolution_rate_last = (resolved_cases_last / total_cases_last * 100) if total_cases_last > 0 else 0

        # =========================
        # PERCENTAGE CHANGE CALCULATIONS
        # =========================
        def percentage_change(current, previous):
            if previous == 0:
                return 0
            return round(((current - previous) / previous) * 100, 2)

        total_cases_change = percentage_change(total_cases, total_cases_last)
        active_cases_change = percentage_change(active_cases, active_cases_last)
        resolved_cases_change = percentage_change(resolved_cases, resolved_cases_last)
        resolution_rate_change = percentage_change(resolution_rate, resolution_rate_last)

        # =========================
        # MONTHLY CASE COUNTS
        # =========================
        monthly_stats = (
            Person.objects
            .filter(_is_deleted=False)
            .annotate(month=TruncMonth('reported_date'))
            .values('month', 'type')
            .annotate(total=Count('id'))
            .order_by('month')
        )

        monthly_summary = {}
        for record in monthly_stats:
            month = record['month'].strftime('%Y-%m') if record['month'] else 'Unknown'
            ptype = record['type']
            count = record['total']
            if month not in monthly_summary:
                monthly_summary[month] = {
                    'Missing Person': 0,
                    'Unidentified Person': 0,
                    'Unidentified Body': 0,
                    'Total': 0,
                }
            monthly_summary[month][ptype] = count
            monthly_summary[month]['Total'] += count

        # =========================
        # CITY-WISE GENDER COUNT
        # =========================
        city_gender_stats = (
            Person.objects
            .filter(city__isnull=False, gender__isnull=False, _is_deleted=False)
            .values('city', 'gender')
            .annotate(count=Count('id'))
            .order_by('city')
        )

        city_summary = {}
        for entry in city_gender_stats:
            city = entry['city']
            gender = entry['gender']
            count = entry['count']
            if city not in city_summary:
                city_summary[city] = {'male': 0, 'female': 0, 'other': 0, 'total': 0}
            city_summary[city][gender] = count
            city_summary[city]['total'] += count

        # =========================
        # RESPONSE DATA
        # =========================
        data = {
            "total_cases": {
                "count": total_cases,
                "change_percent": total_cases_change
            },
            "active_cases": {
                "count": active_cases,
                "change_percent": active_cases_change
            },
            "resolved_cases": {
                "count": resolved_cases,
                "change_percent": resolved_cases_change
            },
            "resolution_rate": {
                "rate": round(resolution_rate, 2),
                "change_percent": resolution_rate_change
            },
            "monthly_summary": monthly_summary,
            "city_gender_summary": city_summary,
        }

        return Response(data)