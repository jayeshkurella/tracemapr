from django.urls import path
from .views import UserCountAPIView
from .views import CaseCountAPIView
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeatureViewSet, RoleFeatureAccessViewSet
from .views import UserFeatureAccessViewSet
from . import views

router = DefaultRouter()
router.register("features", FeatureViewSet, basename="features")
router.register("role-feature-access", RoleFeatureAccessViewSet, basename="role-feature-access")
router.register("user-feature-access", UserFeatureAccessViewSet, basename="user-feature-access")
urlpatterns = [
    path('count/', UserCountAPIView.as_view(), name='user-count'),
    path('case-management/count/', CaseCountAPIView.as_view(), name='case-count'),
    path("", include(router.urls)),
    path('recent-activities/', views.recent_activities, name='recent-activities'),
]
