"""
Created By : Sanket Lodhe
Created Date : July 2025
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from Mainapp.Serializers.serializers import PersonSerializer
from Mainapp.models import Person
from Mainapp.models.person_match_history import PersonMatchHistory
from rest_framework.permissions import AllowAny ,IsAuthenticated




class UnidentifiedPersonMatchWithMPsViewSet(viewsets.ViewSet):
    def get_permissions(self):
        if self.action == 'retrieve':
            return [AllowAny()]
        return [IsAuthenticated()]

    def retrieve(self, request, pk=None):
        try:
            up = Person.objects.get(
                id=pk,
                type='Unidentified Person',
                person_approve_status='approved'
            )
        except Person.DoesNotExist:
            return Response({"error": "Unidentified person not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get history of MPs already seen for this UP
        history_qs = PersonMatchHistory.objects.filter(unidentified_person=up)
        previously_matched_ids = history_qs.values_list('missing_person_id', flat=True)

        # Eligible MPs: approved, not already matched
        eligible_mps = Person.objects.filter(
            type='Missing Person',
            person_approve_status='approved',
            case_status__in=['pending', 'matched']
        ).exclude(id__in=previously_matched_ids)

        newly_matched = []
        new_match_ids = set()

        for mp in eligible_mps:
            score = self.calculate_match_score(mp, up)

            if score == 0:
                continue

            created_by = request.user if request.user.is_authenticated else None

            match_record = PersonMatchHistory.objects.create(
                missing_person=mp,
                unidentified_person=up,
                match_type='matched' if score >= 70 else 'potential',
                score=score,
                match_parameters=self._get_match_parameters(mp, up),
                created_by=created_by,
                is_viewed=False,
            )

            new_match_ids.add(match_record.id)

            if score >= 50:
                newly_matched.append({
                    'person': PersonSerializer(mp).data,
                    'score': score,
                    'match_id': match_record.match_id,
                    'is_viewed': False
                })

        newly_matched.sort(key=lambda x: x['score'], reverse=True)

        # Categorize existing history (excluding newly created matches)
        previously_matched, viewed, rejected, confirmed = [], [], [], []

        for match in history_qs:
            if match.id in new_match_ids:
                continue  # skip newly created matches

            if (match.missing_person.gender and match.unidentified_person.gender and
                    match.missing_person.gender.lower() != match.unidentified_person.gender.lower()):
                continue

            mp_data = PersonSerializer(match.missing_person).data
            match_data = {
                'person': mp_data,
                'score': match.score,
                'match_type': match.match_type,
                'match_id': match.match_id,
                'created_at': match.created_at,
                'is_viewed': match.is_viewed
            }

            if match.is_viewed:
                viewed.append(match_data)
            elif match.match_type == 'matched':
                previously_matched.append(match_data)
            elif match.match_type == 'rejected':
                match_data['reject_reason'] = match.reject_reason
                rejected.append(match_data)
            elif match.match_type == 'confirmed':
                match_data['confirmation_note'] = match.confirmation_note
                confirmed.append(match_data)

        # Sort all
        for group in (previously_matched, viewed, rejected, confirmed):
            group.sort(key=lambda x: x['score'], reverse=True)

        return Response({
            "newly_matched": newly_matched,
            "previously_matched": previously_matched,
            "viewed": viewed,
            "rejected": rejected,
            "confirmed": confirmed,
            "unidentified_person": PersonSerializer(up).data
        })


    def calculate_match_score(self, mp, up):
        score = 0
        gender_mismatch = False

        # Gender check (must match for any potential match)
        if mp.gender and up.gender:
            if mp.gender.lower() != up.gender.lower():
                gender_mismatch = True
            else:
                score += 25  # Gender match points

        # If gender doesn't match, return 0 immediately
        if gender_mismatch:
            return 0

        # Continue with other scoring criteria
        if mp.blood_group and up.blood_group and mp.blood_group.lower() == up.blood_group.lower():
            score += 25

        if mp.complexion and up.complexion and mp.complexion.lower() == up.complexion.lower():
            score += 25

        if mp.hair_color and up.hair_color and mp.hair_color.lower() == up.hair_color.lower():
            score += 25

        if mp.hair_type and up.hair_type and mp.hair_type.lower() == up.hair_type.lower():
            score += 25

        if mp.eye_color and up.eye_color and mp.eye_color.lower() == up.eye_color.lower():
            score += 25

        if mp.age is not None and up.age_range is not None:
            try:
                min_age, max_age = map(int, up.age_range.split('-'))
                if not (min_age <= mp.age <= max_age):
                    return 0  # Reject if age is outside the range
                else:
                    score += 30  # Age matched
            except (ValueError, AttributeError):
                return 0  # Skip if age_range is invalid
        else:
            return 0

            # Height match (25 points max)
        if mp.height_range and up.height_range:
            mp_min, mp_max = self._parse_height_range(mp.height_range)
            up_min, up_max = self._parse_height_range(up.height_range)

            if mp_min is not None and up_min is not None and mp_max is not None and up_max is not None:
                if mp_min <= up_max and mp_max >= up_min:
                    score += 25
                elif (mp_min - 5 <= up_max and mp_max + 5 >= up_min):
                    score += 15
                elif (mp_min - 10 <= up_max and mp_max + 10 >= up_min):
                    score += 5
        elif mp.height is not None and up.height is not None:
            height_diff = abs(mp.height - up.height)
            if height_diff <= 5:
                score += 25
            elif height_diff <= 10:
                score += 15
            elif height_diff <= 20:
                score += 5

        # Weight match (20 points max)
        if mp.weight is not None and up.weight is not None:
            weight_diff = abs(mp.weight - up.weight)
            if weight_diff <= 500:  # 500 grams difference
                score += 20
            elif weight_diff <= 1000:  # 1 kg difference
                score += 10

        if mp.birth_mark and up.birth_mark and mp.birth_mark.lower() == up.birth_mark.lower():
            score += 25

        if mp.distinctive_mark and up.distinctive_mark and mp.distinctive_mark.lower() == up.distinctive_mark.lower():
            score += 25

        return min(score, 100)

    def _parse_height_range(self, height_range):
        try:
            min_h, max_h = map(int, height_range.split('-'))
            return min_h, max_h
        except (ValueError, AttributeError):
            return None, None

    def _get_match_parameters(self, mp, up):
        """
        Returns a dictionary of matching parameters for the history record
        """
        return {
            'gender_match': mp.gender == up.gender,
            'age_match': {
                'mp_age': mp.age,
                'up_age': up.age,
                'up_age_range': up.age_range
            },
            'height_match': {
                'mp_height': mp.height,
                'up_height': up.height,
                'mp_height_range': mp.height_range,
                'up_height_range': up.height_range
            },
            'weight_match': {
                'mp_weight': mp.weight,
                'up_weight': up.weight,
                'difference': abs(mp.weight - up.weight) if mp.weight and up.weight else None
            },
            'complexion_match': mp.complexion == up.complexion,
            'hair_color_match': mp.hair_color == up.hair_color,
            'eye_color_match': mp.eye_color == up.eye_color
        }

    @action(detail=False, methods=['post'], url_path='(?P<match_id>MATCH-[\\w-]+)/mark-viewed')
    def mark_as_viewed(self, request, match_id=None):
        """Mark a single match record as viewed based on match_id in URL."""
        try:
            match = PersonMatchHistory.objects.get(match_id=match_id)
            match.is_viewed = True
            match.save()
            return Response("status changed successfully")
        except PersonMatchHistory.DoesNotExist:
            return Response(
                {"detail": "Match not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], url_path='match-reject')
    def match_reject(self, request, pk=None):
        match_id = request.data.get('match_id')
        reject_reason = request.data.get('reject_reason')

        if not match_id:
            return Response({"error": "match_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not reject_reason:
            return Response({"error": "reject_reason is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Now, match_id is treated as a regular string, not UUID
            match = PersonMatchHistory.objects.get(match_id=match_id, unidentified_person_id=pk)

            if match.match_type in ['confirmed', 'rejected']:
                return Response({"error": f"Match already {match.match_type}."}, status=status.HTTP_400_BAD_REQUEST)

            match.match_type = 'rejected'
            match.reject_reason = reject_reason
            match.is_viewed = False
            match.updated_by = request.user
            match.save()

            return Response({"message": "Match rejected successfully."}, status=status.HTTP_200_OK)

        except PersonMatchHistory.DoesNotExist:
            return Response({"error": "Match not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='match-unreject')
    def match_unreject(self, request, pk=None):
        match_id = request.data.get('match_id')
        new_status = request.data.get('new_status', 'matched')
        unreject_reason = request.data.get('unreject_reason')

        if not match_id:
            return Response({"error": "match_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        if new_status not in ['matched', 'potential']:
            return Response({"error": "Invalid new_status. Use 'matched' or 'potential'."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not unreject_reason:
            return Response({"error": "unreject_reason is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            match = PersonMatchHistory.objects.get(match_id=match_id, unidentified_person_id=pk)

            if match.match_type != 'rejected':
                return Response({"error": f"Match is not rejected. Current status is {match.match_type}."},
                                status=status.HTTP_400_BAD_REQUEST)

            match.match_type = new_status
            match.reject_reason = None
            match.unreject_reason = unreject_reason
            match.is_viewed = True
            match.updated_by = request.user
            match.save()

            return Response({"message": f"Match status reverted to '{new_status}' successfully."},
                            status=status.HTTP_200_OK)

        except PersonMatchHistory.DoesNotExist:
            return Response({"error": "Match not found."}, status=status.HTTP_404_NOT_FOUND)

    # To confirm the match between missing person and unidentified persons
    @action(detail=True, methods=['post'], url_path='match-confirm')
    def match_confirm(self, request, pk=None):
        match_id = request.data.get('match_id')
        confirmation_note = request.data.get('confirmation_note', '')
        confirmed_from = request.data.get("confirmed_from")

        if not match_id:
            return Response({"error": "match_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not confirmed_from or confirmed_from not in ["MP", "UP", "UB"]:
            return Response({"error": "confirmed_from is required (MP/UP/UB)."}, status=status.HTTP_400_BAD_REQUEST)


        try:
            match = PersonMatchHistory.objects.get(match_id=match_id, unidentified_person_id=pk)

            if match.match_type in ['confirmed', 'rejected']:
                return Response({"error": f"Match already {match.match_type}."}, status=status.HTTP_400_BAD_REQUEST)

            #  Prevent duplicate confirmations
            if match.missing_person.case_status == 'resolved':
                return Response(
                    {"error": "This Missing Person is already resolved with another Unidentified Person."},
                    status=status.HTTP_400_BAD_REQUEST)

            if match.unidentified_person.case_status == 'resolved':
                return Response(
                    {"error": "This Unidentified Person is already resolved with another Missing Person."},
                    status=status.HTTP_400_BAD_REQUEST)

            # Update match record
            match.match_type = 'confirmed'
            match.confirmation_note = confirmation_note
            match.match_with = 'Missing Person'
            match.is_viewed = False
            match.updated_by = request.user
            match.save()

            mp = match.missing_person
            up = match.unidentified_person

            mp.case_status = 'resolved'
            mp.updated_by = request.user
            mp.match_with = 'Unidentified Person'
            mp.matched_case_id = up.case_id
            mp.matched_person_id = up.id
            mp.matched_case_id = up.case_id
            mp.confirmed_from =confirmed_from
            mp.save()
            up.case_status = 'resolved'
            up.match_with = 'Missing Person'
            up.matched_case_id = mp.case_id
            up.matched_person_id = mp.id
            up.matched_case_id = mp.case_id
            up.confirmed_from=confirmed_from
            up.updated_by = request.user
            up.save()

            return Response({"message": "Match confirmed successfully."}, status=status.HTTP_200_OK)

        except PersonMatchHistory.DoesNotExist:
            return Response({"error": "Match not found."}, status=status.HTTP_404_NOT_FOUND)

    # To un confirm the match between missing person and unidentified persons
    @action(detail=True, methods=['post'], url_path='match-unconfirm')
    def match_unconfirm(self, request, pk=None):
        print("data from api",request.data)
        new_status = request.data.get('new_status', 'matched')
        reason = request.data.get('unconfirm_reason')
        matched_person = request.data.get('matched_person_id')

        if not matched_person:
            return Response({"error": "Mising person id is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not reason:
            return Response({"error": "unconfirm_reason is required."}, status=status.HTTP_400_BAD_REQUEST)

        if new_status not in ['matched', 'potential']:
            return Response({"error": "Invalid new_status. Use 'matched' or 'potential'."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            match = PersonMatchHistory.objects.filter(missing_person=matched_person,unidentified_person_id=pk).first()
            print("current status",match.match_type)
            print("person id",match.unidentified_person)
            if match.match_type != 'confirmed':
                return Response({"error": f"Match is not confirmed. Current status is {match.match_type}."},
                                status=status.HTTP_400_BAD_REQUEST)

            match.match_type = new_status
            match.confirmation_note = None
            match.unconfirm_reason = reason
            match.updated_by = request.user
            match.is_viewed = True
            match.save()

            # Reset MP (missing person)
            mp = match.missing_person
            mp.case_status = 'pending'
            mp.match_with = None
            mp.matched_person_id = None
            mp.matched_case_id = None
            mp.updated_by = request.user
            mp.confirmed_from=None
            mp.save()

            # Reset UP (unidentified person)
            up = match.unidentified_person
            up.case_status = 'pending'
            up.match_with = None
            up.matched_person_id = None
            up.matched_case_id =None
            up.confirmed_from=None
            up.updated_by = request.user

            up.save()

            return Response({"message": f"Match unconfirmed. Status reverted to '{new_status}'."},
                            status=status.HTTP_200_OK)

        except PersonMatchHistory.DoesNotExist:
            return Response({"error": "Match not found."}, status=status.HTTP_404_NOT_FOUND)

