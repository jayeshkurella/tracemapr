

"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""



from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

from .Additional_info_Tags.tags_apis import CasteListCreateAPIView, CasteDestroyAPIView, educationaltagAPIView, \
    occupationtagAPIView
from .authentication.admin_user_management import AdminUserApprovalView, ApprovedUsersView, HoldUsersView, \
    RejectedUsersView
from .authentication.user_authentication import AuthAPIView,UserListAPIView
from .matching_apis.match_missing_with_unidentified_body import MissingPersonMatchWithUBsViewSet
from .matching_apis.match_unidentified_body_with_mp import UnidentifiedBodyMatchWithMPsViewSet
from .matching_apis.match_unidentified_person_with_mp import UnidentifiedPersonMatchWithMPsViewSet
from .viewsets.casetype_apis import PendingPersonsView, ApprovedPersonsView, RejectedPersonsView, OnHoldPersonsView, \
    SuspendedPersonsView, StatusCountView
from .viewsets.fetch_by_id_Case import RetrieveUnfilteredPersonView
from .viewsets.filters import filter_Address_ViewSet
from .viewsets.hospital import HospitalViewSet, HospitalListView, GovtHospitalListView
from .viewsets.person_api import PersonViewSet
from .viewsets.police_station import PoliceStationViewSet, PoliceStationListView, police_station_search

from .matching_apis.missing_match_up import MissingPersonMatchWithUPsViewSet
from .viewsets.statistics import PersonStatisticsAPIView
from .viewsets.volunteer import VolunteerViewSet
from .viewsets.change_log import ChangeLogViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


router = DefaultRouter()

# to get , post and update of person and body details
router.register(r'persons', PersonViewSet, basename='person')
router.register(r'police-stations', PoliceStationViewSet, basename='police-station')
router.register(r'hospitals', HospitalViewSet, basename='hospital')
router.register(r'filters_address', filter_Address_ViewSet, basename='filters')
router.register(r'volunteers',VolunteerViewSet,basename='volunteer')
router.register(r'changelogs', ChangeLogViewSet ,basename='chnagelog')

# match data between missing person and Unidentified Persons
router.register(r'missing-person-with-ups', MissingPersonMatchWithUPsViewSet ,basename='missing-person-with-ups')

# match data between missing person and Unidentified Bodies
router.register(r'missing-person-with-ubs', MissingPersonMatchWithUBsViewSet ,basename='missing-person-with-ubs')

# match data between Unidentified Person and Missing persons
router.register(r'unidentified_person-with-mps', UnidentifiedPersonMatchWithMPsViewSet ,basename='unidentified_person-with-mps')

# match data between Unidentified body and Missing persons
router.register(r'unidentified_bodies-with-mps', UnidentifiedBodyMatchWithMPsViewSet ,basename='unidentified_bodies-with-mps')


urlpatterns = [
    path('api/', include(router.urls)),
    path('api/users/', AuthAPIView.as_view(), name='user-auth'),
    path("users/", UserListAPIView.as_view(), name="user-list"),
    path('reset-password/<str:reset_token>/', AuthAPIView.as_view(), name='reset-password-get'),
    path('reset-password/', AuthAPIView.as_view(), name='reset-password-post'),
    path("api/hospital-name-list/", HospitalListView.as_view(), name="hospital-list"),
    path("api/govt-hospital-name-list/", GovtHospitalListView.as_view(), name="govt-hospital-list"),
    path("api/police-station-name-list/", PoliceStationListView.as_view(), name="police-station-list"),
    path('api/police-station-search/', police_station_search, name='police_station_search'),
    path("api/pending-users/", AdminUserApprovalView.as_view(), name="pending-users"),
    path('api/users/approved/', ApprovedUsersView.as_view(), name='approved-users'),
    path('api/users/hold/', HoldUsersView.as_view(), name='hold-users'),
    path('api/users/rejected/', RejectedUsersView.as_view(), name='rejected-users'),
    path("api/users/approve/<uuid:user_id>/", AdminUserApprovalView.as_view(), name="admin-approve-user"),
    path('api/persons_status/pending/', PendingPersonsView.as_view(), name='pending-persons'),
    path('api/persons_status/approved/', ApprovedPersonsView.as_view(), name='approved-persons'),
    path('api/persons_status/rejected/', RejectedPersonsView.as_view(), name='rejected-persons'),
    path('api/persons_status/on_hold/', OnHoldPersonsView.as_view(), name='on-hold-persons'),
    path('api/persons_status/suspended/', SuspendedPersonsView.as_view(), name='suspended-persons'),
    path('api/persons_status/status_counts/', StatusCountView.as_view(), name='status-counts'),
    path('api/castes_tags/', CasteListCreateAPIView.as_view(), name='caste-list-create'),
    path('api/educational_tags/', educationaltagAPIView.as_view(), name='educational-list-create'),
    path('api/occupation_tags/', occupationtagAPIView.as_view(), name='occupation-list-create'),
    path('api/case/<uuid:pk>/admin-retrieve/', RetrieveUnfilteredPersonView.as_view(), name='admin-retrieve-person'),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
path('api/person/statistics/', PersonStatisticsAPIView.as_view(), name='person-statistics'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
