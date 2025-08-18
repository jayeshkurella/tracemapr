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
from Mainapp.models.match_missing_with_unidentified_body import Missing_match_with_body

from rest_framework.permissions import AllowAny ,IsAuthenticated


class MissingPersonMatchWithUBsViewSet(viewsets.ViewSet):
    def get_permissions(self):
        if self.action == 'retrieve':
            return [AllowAny()]
        return [IsAuthenticated()]

    def retrieve(self, request, pk=None):
        try:
            missing_person = Person.objects.get(
                id=pk,
                type='Missing Person',
                person_approve_status='approved'
            )
        except Person.DoesNotExist:
            return Response({"error": "Missing person not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get previously matched/rejected/confirmed ubs for this MP
        history_qs = Missing_match_with_body.objects.filter(missing_person=missing_person)
        previously_matched_ids = history_qs.values_list('unidentified_bodies_id', flat=True)


        # Get eligible ubs (excluding ones seen before for this MP)
        eligible_ubs = Person.objects.filter(
            type='Unidentified Body',
            person_approve_status='approved',
            case_status__in=['pending', 'matched']
        ).exclude(id__in=previously_matched_ids)

        # Calculate scores and find matches
        newly_matched = []
        new_match_ids = set()
        for ub in eligible_ubs:
            score = self.calculate_match_score(missing_person, ub)

            # Skip if gender doesn't match (score will be 0)
            if score == 0:
                continue

            created_by = request.user if request.user.is_authenticated else None

            # Create match history record
            match_record = Missing_match_with_body.objects.create(
                missing_person=missing_person,
                unidentified_bodies=ub,
                match_type='matched' if score >= 70 else 'potential',
                score=score,
                match_parameters=self._get_match_parameters(missing_person, ub),
                created_by=created_by,
                is_viewed=False,
            )

            new_match_ids.add(match_record.id)

            if score >= 50:
                newly_matched.append({
                    'Body': PersonSerializer(ub).data,
                    'score': score,
                    'match_id': match_record.match_id,
                    'is_viewed': False
                })

        # Sort newly_matched by score (highest first)
        newly_matched.sort(key=lambda x: x['score'], reverse=True)

        # Categorize previously matched ones with scores
        previously_matched = []
        viewed = []
        rejected = []
        confirmed = []

        for match in history_qs:
            if match.id in new_match_ids:
                continue  # skip newly created matches
            if (match.missing_person.gender and match.unidentified_bodies.gender and
                    match.missing_person.gender.lower() != match.unidentified_bodies.gender.lower()):
                continue

            ub_data = PersonSerializer(match.unidentified_bodies).data
            match_data = {
                'Body': ub_data,
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


        # Sort all lists by score (highest first)
        previously_matched.sort(key=lambda x: x['score'], reverse=True)
        viewed.sort(key=lambda x: x['score'], reverse=True)
        rejected.sort(key=lambda x: x['score'], reverse=True)
        confirmed.sort(key=lambda x: x['score'], reverse=True)

        return Response({
            "newly_matched": newly_matched,
            "previously_matched": previously_matched,
            "viewed": viewed,
            "rejected": rejected,
            "confirmed": confirmed,
            "missing_person": PersonSerializer(missing_person).data
        })

    def calculate_match_score(self, mp, ub):
        score = 0
        gender_mismatch = False

        # Gender check (must match for any potential match)
        if mp.gender and ub.gender:
            if mp.gender.lower() != ub.gender.lower():
                gender_mismatch = True
            else:
                score += 25  # Gender match points

        # If gender doesn't match, return 0 immediately
        if gender_mismatch:
            return 0

        # Continue with other scoring criteria
        if mp.blood_group and ub.blood_group and mp.blood_group.lower() == ub.blood_group.lower():
            score += 25

        if mp.complexion and ub.complexion and mp.complexion.lower() == ub.complexion.lower():
            score += 25

        if mp.hair_color and ub.hair_color and mp.hair_color.lower() == ub.hair_color.lower():
            score += 25

        if mp.hair_type and ub.hair_type and mp.hair_type.lower() == ub.hair_type.lower():
            score += 25

        if mp.eye_color and ub.eye_color and mp.eye_color.lower() == ub.eye_color.lower():
            score += 25


        if mp.age is not None and ub.age_range is not None:
            try:
                min_age, max_age = map(int, ub.age_range.split('-'))
                if not (min_age <= mp.age <= max_age):
                    return 0  # Reject if age is outside the range
                else:
                    score += 30  # Age matched
            except (ValueError, AttributeError):
                return 0  # Skip if age_range is invalid
        else:
            return 0



            # Height match (25 points max)
        if mp.height_range and ub.height_range:
            mp_min, mp_max = self._parse_height_range(mp.height_range)
            ub_min, ub_max = self._parse_height_range(ub.height_range)

            if mp_min is not None and ub_min is not None and mp_max is not None and ub_max is not None:
                if mp_min <= ub_max and mp_max >= ub_min:
                    score += 25
                elif (mp_min - 5 <= ub_max and mp_max + 5 >= ub_min):
                    score += 15
                elif (mp_min - 10 <= ub_max and mp_max + 10 >= ub_min):
                    score += 5
        elif mp.height is not None and ub.height is not None:
            height_diff = abs(mp.height - ub.height)
            if height_diff <= 5:
                score += 25
            elif height_diff <= 10:
                score += 15
            elif height_diff <= 20:
                score += 5

        # Weight match (20 points max)
        if mp.weight is not None and ub.weight is not None:
            weight_diff = abs(mp.weight - ub.weight)
            if weight_diff <= 500:  # 500 grams difference
                score += 20
            elif weight_diff <= 1000:  # 1 kg difference
                score += 10

        if mp.birth_mark and ub.birth_mark and mp.birth_mark.lower() == ub.birth_mark.lower():
            score += 25

        if mp.distinctive_mark and ub.distinctive_mark and mp.distinctive_mark.lower() == ub.distinctive_mark.lower():
            score += 25

        return min(score, 100)

    def _parse_height_range(self, height_range):
        try:
            min_h, max_h = map(int, height_range.split('-'))
            return min_h, max_h
        except (ValueError, AttributeError):
            return None, None

    def _get_match_parameters(self, mp, ub):
        """
        Returns a dictionary of matching parameters for the history record
        """
        return {
            'gender_match': mp.gender == ub.gender,
            'age_match': {
                'mp_age': mp.age,
                'ub_age': ub.age,
                'ub_age_range': ub.age_range
            },
            'height_match': {
                'mp_height': mp.height,
                'ub_height': ub.height,
                'mp_height_range': mp.height_range,
                'ub_height_range': ub.height_range
            },
            'weight_match': {
                'mp_weight': mp.weight,
                'ub_weight': ub.weight,
                'difference': abs(mp.weight - ub.weight) if mp.weight and ub.weight else None
            },
            'complexion_match': mp.complexion == ub.complexion,
            'hair_color_match': mp.hair_color == ub.hair_color,
            'eye_color_match': mp.eye_color == ub.eye_color
        }

    @action(detail=True, methods=['post'], url_path='match-reject')
    def match_reject_ub(self, request, pk=None):
        match_id = request.data.get('match_id')
        reject_reason = request.data.get('reject_reason')

        if not match_id:
            return Response({"error": "match_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not reject_reason:
            return Response({"error": "reject_reason is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Now, match_id is treated as a regular string, not UUID
            match = Missing_match_with_body.objects.get(match_id=match_id, missing_person_id=pk)

            if match.match_type in ['confirmed', 'rejected']:
                return Response({"error": f"Match already {match.match_type}."}, status=status.HTTP_400_BAD_REQUEST)

            match.match_type = 'rejected'
            match.reject_reason = reject_reason
            match.is_viewed = False
            match.updated_by = request.user
            match.save()

            return Response({"message": "Match rejected successfully."}, status=status.HTTP_200_OK)

        except Missing_match_with_body.DoesNotExist:
            return Response({"error": "Match not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='match-unreject')
    def match_unreject_ub(self, request, pk=None):
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
            match = Missing_match_with_body.objects.get(match_id=match_id, missing_person_id=pk)

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

        except Missing_match_with_body.DoesNotExist:
            return Response({"error": "Match not found."}, status=status.HTTP_404_NOT_FOUND)

    # To confirm the match between missing person and unidentified persons
    @action(detail=True, methods=['post'], url_path='match-confirm')
    def match_confirm_up(self, request, pk=None):
        match_id = request.data.get('match_id')
        confirmation_note = request.data.get('confirmation_note', '')

        if not match_id:
            return Response({"error": "match_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            match = Missing_match_with_body.objects.get(match_id=match_id, missing_person_id=pk)

            if match.match_type in ['confirmed', 'rejected']:
                return Response({"error": f"Match already {match.match_type}."}, status=status.HTTP_400_BAD_REQUEST)

            # ubdate match record
            match.match_type = 'confirmed'
            match.confirmation_note = confirmation_note
            match.match_with = 'Unidentified Body'
            match.is_viewed = False
            match.updated_by = request.user
            match.save()

            mp = match.missing_person
            ub = match.unidentified_bodies

            mp.case_status = 'resolved'
            mp.updated_by = request.user
            mp.match_with = 'Unidentified Body'
            mp.matched_person_id = ub.id
            mp.save()
            ub.case_status = 'resolved'
            ub.match_with = 'Missing Person'
            ub.matched_person_id = mp.id
            ub.updated_by = request.user
            ub.save()

            return Response({"message": "Match confirmed successfully."}, status=status.HTTP_200_OK)

        except Missing_match_with_body.DoesNotExist:
            return Response({"error": "Match not found."}, status=status.HTTP_404_NOT_FOUND)

    # To un confirm the match between missing person and unidentified persons
    @action(detail=True, methods=['post'], url_path='match-unconfirm')
    def match_unconfirm_ub(self, request, pk=None):
        matched_person = request.data.get('matched_person_id')
        new_status = request.data.get('new_status', 'matched')
        reason = request.data.get('unconfirm_reason')

        if not matched_person:
            return Response({"error": "Unidentified body id is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not reason:
            return Response({"error": "unconfirm_reason is required."}, status=status.HTTP_400_BAD_REQUEST)

        if new_status not in ['matched', 'potential']:
            return Response({"error": "Invalid new_status. Use 'matched' or 'potential'."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # match = Missing_match_with_body.objects.get(match_id=match_id, missing_person_id=pk)
            match = Missing_match_with_body.objects.filter(unidentified_body=matched_person,missing_person_id=pk).first()

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
            mp.updated_by = request.user
            mp.save()

            # Reset ub (unidentified person)
            ub = match.unidentified_bodies
            ub.case_status = 'pending'
            ub.match_with = None
            ub.matched_person_id = None
            ub.updated_by = request.user

            ub.save()

            return Response({"message": f"Match unconfirmed. Status reverted to '{new_status}'."},
                            status=status.HTTP_200_OK)

        except Missing_match_with_body.DoesNotExist:
            return Response({"error": "Match not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='(?P<match_id>MATCH-[\\w-]+)/mark-viewed')
    def mark_as_viewed_up(self, request, match_id=None):
        """Mark a single match record as viewed based on match_id in URL."""
        try:
            match = Missing_match_with_body.objects.get(match_id=match_id)
            match.is_viewed = True
            match.updated_by = request.user
            match.save()
            return Response("status changed successfully")
        except Missing_match_with_body.DoesNotExist:
            return Response(
                {"detail": "Match not found."},
                status=status.HTTP_404_NOT_FOUND
            )