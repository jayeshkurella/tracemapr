from django.urls import path
from .views import UserCountAPIView
from .views import CaseCountAPIView

urlpatterns = [
    path('user-management/count/', UserCountAPIView.as_view(), name='user-count'),
    path('case-management/count/', CaseCountAPIView.as_view(), name='case-count'),
]
