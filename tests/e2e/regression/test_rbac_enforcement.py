"""
Regression Tests: Phase 4 RBAC Enforcement

Validates state-based access control is working correctly.

Protected Views:
- Detail view: only EMPLOYER_INTEREST_VIEW and beyond
- Interessar: only from EMPLOYER_INTEREST_VIEW
- Declinar: only from EMPLOYER_INTEREST_VIEW
- Liberar Contato: only from MATCHED+
- Responder: only from CONTACT_ENABLED+
"""

import pytest
from matchco.recruitment.models import Relation


class TestRBACDetailViewAccess:
    """Test detail view access control by relation state"""

    @pytest.mark.regression
    def test_cannot_view_notice_delivered(self, client, relation_notice_delivered):
        """Test: Cannot view relation in NOTICE_DELIVERED state"""

        response = client.get(f'/portal/relation/{relation_notice_delivered.id}/')

        assert response.status_code == 403, \
            f"Got {response.status_code}, expected 403 (Forbidden)"
        assert "manifestar interesse" in response.content.decode().lower(), \
            "Error message should mention 'manifestar interesse'"

    @pytest.mark.regression
    def test_cannot_view_notice_expired(self, django_db_blocker, client):
        """Test: Cannot view relation in NOTICE_EXPIRED state"""

        with django_db_blocker.unblock():
            relation = Relation.objects.create(
                state=Relation.STATE_NOTICE_EXPIRED,
            )

        response = client.get(f'/portal/relation/{relation.id}/')

        assert response.status_code == 403, \
            "Should forbid access to expired notices"

    @pytest.mark.regression
    def test_can_view_employer_interest_view(self, client, relation_employer_interest_view):
        """Test: Can view relation in EMPLOYER_INTEREST_VIEW state"""

        response = client.get(f'/portal/relation/{relation_employer_interest_view.id}/')

        assert response.status_code == 200, \
            "Should allow viewing in EMPLOYER_INTEREST_VIEW state"
        assert "candidate" in response.content.decode().lower(), \
            "Should display candidate information"

    @pytest.mark.regression
    def test_can_view_employer_interested(self, django_db_blocker, client):
        """Test: Can view relation in EMPLOYER_INTERESTED state"""

        with django_db_blocker.unblock():
            relation = Relation.objects.create(
                state=Relation.STATE_EMPLOYER_INTERESTED,
            )

        response = client.get(f'/portal/relation/{relation.id}/')
        assert response.status_code == 200

    @pytest.mark.regression
    def test_can_view_matched(self, client, relation_matched):
        """Test: Can view relation in MATCHED state"""

        response = client.get(f'/portal/relation/{relation_matched.id}/')
        assert response.status_code == 200

    @pytest.mark.regression
    def test_can_view_contact_enabled(self, django_db_blocker, client):
        """Test: Can view relation in CONTACT_ENABLED state"""

        with django_db_blocker.unblock():
            relation = Relation.objects.create(
                state=Relation.STATE_CONTACT_ENABLED,
            )

        response = client.get(f'/portal/relation/{relation.id}/')
        assert response.status_code == 200

    @pytest.mark.regression
    def test_can_view_response_created(self, django_db_blocker, client):
        """Test: Can view relation in RESPONSE_CREATED state"""

        with django_db_blocker.unblock():
            relation = Relation.objects.create(
                state=Relation.STATE_RESPONSE_CREATED,
            )

        response = client.get(f'/portal/relation/{relation.id}/')
        assert response.status_code == 200


class TestRBACInteressarAction:
    """Test declaring interest (Interessar) action access"""

    @pytest.mark.regression
    def test_cannot_interessar_from_notice_delivered(self, django_db_blocker, client):
        """Test: Cannot declare interest from NOTICE_DELIVERED"""

        with django_db_blocker.unblock():
            relation = Relation.objects.create(
                state=Relation.STATE_NOTICE_DELIVERED,
            )

        response = client.post(f'/portal/relation/{relation.id}/interessar/')

        # Should redirect with error message
        assert response.status_code == 302 or response.status_code == 403, \
            f"Got {response.status_code}"

    @pytest.mark.regression
    def test_cannot_interessar_from_employer_interested(self, django_db_blocker, client):
        """Test: Cannot declare interest twice (wrong state)"""

        with django_db_blocker.unblock():
            relation = Relation.objects.create(
                state=Relation.STATE_EMPLOYER_INTERESTED,
            )

        response = client.post(f'/portal/relation/{relation.id}/interessar/')

        assert response.status_code in [302, 403], \
            "Should prevent interest declaration from wrong state"

    @pytest.mark.regression
    def test_can_interessar_from_employer_interest_view(self, client, relation_employer_interest_view):
        """Test: Can declare interest from EMPLOYER_INTEREST_VIEW"""

        response = client.post(f'/portal/relation/{relation_employer_interest_view.id}/interessar/')

        # Should succeed (302 redirect or 200)
        assert response.status_code in [200, 302], \
            f"Got {response.status_code}, expected success"

        # Verify state transition in database
        with pytest.raises(Exception):  # Force DB access
            pass
        relation_employer_interest_view.refresh_from_db()
        assert relation_employer_interest_view.state == Relation.STATE_EMPLOYER_INTERESTED


class TestRBACDeclinarAction:
    """Test declaring disinterest (Declinar) action access"""

    @pytest.mark.regression
    def test_cannot_declinar_from_notice_delivered(self, django_db_blocker, client):
        """Test: Cannot decline from NOTICE_DELIVERED"""

        with django_db_blocker.unblock():
            relation = Relation.objects.create(
                state=Relation.STATE_NOTICE_DELIVERED,
            )

        response = client.post(f'/portal/relation/{relation.id}/declinar/')

        assert response.status_code in [302, 403]

    @pytest.mark.regression
    def test_can_declinar_from_employer_interest_view(self, client, relation_employer_interest_view):
        """Test: Can decline from EMPLOYER_INTEREST_VIEW"""

        response = client.post(f'/portal/relation/{relation_employer_interest_view.id}/declinar/')

        assert response.status_code in [200, 302]

        # Verify state transition
        relation_employer_interest_view.refresh_from_db()
        assert relation_employer_interest_view.state == Relation.STATE_NO_EMPLOYER_INTEREST

    @pytest.mark.regression
    def test_cannot_declinar_from_matched(self, client, relation_matched):
        """Test: Cannot decline after already matched"""

        response = client.post(f'/portal/relation/{relation_matched.id}/declinar/')

        assert response.status_code in [302, 403], \
            "Cannot decline after bilateral match"


class TestRBACLiberarContatoAction:
    """Test enabling contact (Liberar Contato) action access"""

    @pytest.mark.regression
    def test_cannot_liberar_contato_from_employer_interest_view(self, client, relation_employer_interest_view):
        """Test: Cannot enable contact before bilateral match"""

        response = client.post(f'/portal/relation/{relation_employer_interest_view.id}/liberar-contato/')

        assert response.status_code in [302, 403]

    @pytest.mark.regression
    def test_cannot_liberar_contato_from_employer_interested(self, django_db_blocker, client):
        """Test: Cannot enable contact before bilateral match (employer interested, not matched)"""

        with django_db_blocker.unblock():
            relation = Relation.objects.create(
                state=Relation.STATE_EMPLOYER_INTERESTED,
            )

        response = client.post(f'/portal/relation/{relation.id}/liberar-contato/')

        assert response.status_code in [302, 403], \
            "Should require bilateral match before enabling contact"

    @pytest.mark.regression
    def test_can_liberar_contato_from_matched(self, client, relation_matched):
        """Test: Can enable contact after MATCHED"""

        response = client.post(f'/portal/relation/{relation_matched.id}/liberar-contato/')

        assert response.status_code in [200, 302]

        # Verify state transition
        relation_matched.refresh_from_db()
        assert relation_matched.state == Relation.STATE_CONTACT_ENABLED

    @pytest.mark.regression
    def test_can_liberar_contato_from_contact_enabled(self, django_db_blocker, client):
        """Test: Can enable contact again from CONTACT_ENABLED (idempotent)"""

        with django_db_blocker.unblock():
            relation = Relation.objects.create(
                state=Relation.STATE_CONTACT_ENABLED,
            )

        response = client.post(f'/portal/relation/{relation.id}/liberar-contato/')

        # Should not error (idempotent operation)
        assert response.status_code in [200, 302]


class TestRBACResponderAction:
    """Test sending response action access"""

    @pytest.mark.regression
    def test_cannot_responder_from_employer_interest_view(self, client, relation_employer_interest_view):
        """Test: Cannot send response before contact enabled"""

        response = client.post(
            f'/portal/relation/{relation_employer_interest_view.id}/responder/',
            {"message": "Test response"}
        )

        assert response.status_code in [302, 403]

    @pytest.mark.regression
    def test_cannot_responder_from_matched(self, client, relation_matched):
        """Test: Cannot send response before contact channel opened"""

        response = client.post(
            f'/portal/relation/{relation_matched.id}/responder/',
            {"message": "Test response"}
        )

        assert response.status_code in [302, 403], \
            "Should require contact enabled before responding"

    @pytest.mark.regression
    def test_can_responder_from_contact_enabled(self, django_db_blocker, client):
        """Test: Can send response after contact enabled"""

        with django_db_blocker.unblock():
            relation = Relation.objects.create(
                state=Relation.STATE_CONTACT_ENABLED,
            )

        response = client.post(
            f'/portal/relation/{relation.id}/responder/',
            {"message": "Test response"}
        )

        assert response.status_code in [200, 302]

        # Verify state transition
        relation.refresh_from_db()
        assert relation.state == Relation.STATE_RESPONSE_CREATED


class TestRBACStateTransitionMatrix:
    """Test complete state transition matrix"""

    @pytest.mark.regression
    def test_complete_matching_flow(self, django_db_blocker, client):
        """Test: Complete flow from NOTICE to CONTACT_ENABLED"""

        with django_db_blocker.unblock():
            relation = Relation.objects.create(
                state=Relation.STATE_NOTICE_DELIVERED,
            )

        # Step 1: Cannot view or act on NOTICE_DELIVERED
        response = client.get(f'/portal/relation/{relation.id}/')
        assert response.status_code == 403

        # Step 2: Transition to EMPLOYER_INTEREST_VIEW (simulated by candidate interest)
        with django_db_blocker.unblock():
            relation.state = Relation.STATE_EMPLOYER_INTEREST_VIEW
            relation.save()

        # Now can view
        response = client.get(f'/portal/relation/{relation.id}/')
        assert response.status_code == 200

        # Step 3: Declare interest
        response = client.post(f'/portal/relation/{relation.id}/interessar/')
        with django_db_blocker.unblock():
            relation.refresh_from_db()
            assert relation.state == Relation.STATE_EMPLOYER_INTERESTED

        # Step 4: Transition to MATCHED (simulated by candidate interest)
        with django_db_blocker.unblock():
            relation.state = Relation.STATE_MATCHED
            relation.save()

        # Step 5: Enable contact
        response = client.post(f'/portal/relation/{relation.id}/liberar-contato/')
        with django_db_blocker.unblock():
            relation.refresh_from_db()
            assert relation.state == Relation.STATE_CONTACT_ENABLED

        # Step 6: Send response
        response = client.post(
            f'/portal/relation/{relation.id}/responder/',
            {"message": "Response"}
        )
        with django_db_blocker.unblock():
            relation.refresh_from_db()
            assert relation.state == Relation.STATE_RESPONSE_CREATED
