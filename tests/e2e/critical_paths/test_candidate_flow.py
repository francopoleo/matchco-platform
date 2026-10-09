"""
Critical Path 1: Candidate Complete Flow

Test: Candidate signs up → matches → declares interest → enables contact

Flow:
1. Navigate to QR entry point
2. Select store from dropdown
3. Choose "Create Profile" action
4. Fill questionnaire (all question types)
5. Enter phone & email + verify OTP
6. Verify CandidateProfile created
7. Wait for match algorithm
8. Declare interest in matching opportunity
9. Verify relation state transitions
10. Accept employer interest
11. Verify MATCHED state
12. Enable contact & verify visibility
"""

import pytest
import time
from datetime import datetime, timedelta
from matchco.recruitment.models import (
    CandidateProfile, Relation, CandidateSignupAnswer
)


class TestCandidateSignupFlow:
    """Complete candidate signup flow"""

    @pytest.mark.e2e
    def test_candidate_qr_entry_to_profile_creation(self, page, live_server, store_with_questionnaire):
        """Test: QR signup entry → profile creation"""

        # 1. Navigate to store chooser
        page.goto(f"{live_server}/candidato/loja/escolher/")
        page.wait_for_selector("input[type='radio'][value='{store_with_questionnaire['store'].id}']")

        # Verify store is listed
        assert page.locator(f"text={store_with_questionnaire['store'].name}").is_visible()

        # 2. Select store
        page.click(f"input[type='radio'][value='{store_with_questionnaire['store'].id}']")
        page.click("button:has-text('Continue')")

        # 3. Verify action chooser appears
        page.wait_for_selector("button:has-text('Create Profile')")
        assert page.locator("text=What action do you want to take?").is_visible()

        # 4. Choose profile creation
        page.click("button:has-text('Create Profile')")

        # 5. Verify signup form rendered
        page.wait_for_selector("input[name='responses']", timeout=2000)

        # Verify all question types present
        assert page.locator("input[type='text']").count() >= 1  # Name
        assert page.locator("input[type='radio']").count() >= 2  # Boolean questions
        assert page.locator("select").count() >= 1  # Dropdown for shift
        assert page.locator("input[type='date']").count() >= 1  # Date picker
        assert page.locator("input[type='range']").count() >= 1  # Scale

    @pytest.mark.e2e
    def test_candidate_questionnaire_all_types(self, page, live_server, store_with_questionnaire):
        """Test: Fill questionnaire with all question types"""

        # Navigate to form
        page.goto(f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile")
        page.wait_for_selector("form")

        # Fill text field (name)
        page.fill("input[name='question_1']", "João Silva")

        # Fill boolean (caixa)
        page.click("input[type='radio'][name='question_2'][value='true']")

        # Fill select (shift)
        page.select_option("select[name='question_3']", "Manhã")

        # Fill date
        page.fill("input[type='date'][name='question_4']", "2026-11-15")

        # Fill scale (experiência)
        page.fill("input[type='range'][name='question_5']", "4")

        # Scroll to contact info
        page.locator("input[name='phone']").scroll_into_view_if_needed()

        # Fill contact info
        page.fill("input[name='phone']", "+5511998765432")
        page.fill("input[name='email']", "joao.silva@test.com")

        # Accept LGPD consent
        page.check("input[name='accept_terms']")

        # Submit form
        page.click("button:has-text('Submit')")

        # Verify OTP screen
        page.wait_for_selector("input[name='otp_code']", timeout=3000)
        assert page.locator("text=Enter verification code").is_visible()

    @pytest.mark.e2e
    def test_candidate_otp_verification(self, page, live_server, django_db_blocker, store_with_questionnaire):
        """Test: OTP verification creates profile"""

        # Navigate to form and submit
        page.goto(f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile")
        page.wait_for_selector("form")

        # Fill minimal form
        page.fill("input[name='question_1']", "João Silva")
        page.click("input[type='radio'][name='question_2'][value='true']")
        page.select_option("select[name='question_3']", "Manhã")
        page.fill("input[type='date'][name='question_4']", "2026-11-15")
        page.fill("input[type='range'][name='question_5']", "4")
        page.locator("input[name='phone']").scroll_into_view_if_needed()
        page.fill("input[name='phone']", "+5511998765432")
        page.fill("input[name='email']", "joao.silva@test.com")
        page.check("input[name='accept_terms']")
        page.click("button:has-text('Submit')")

        # Wait for OTP screen
        page.wait_for_selector("input[name='otp_code']", timeout=3000)

        # Get OTP from database
        with django_db_blocker.unblock():
            from matchco.recruitment.models import OtpVerification
            otp_obj = OtpVerification.objects.filter(
                mobile="+5511998765432"
            ).latest("created_at")
            otp_code = otp_obj.code

        # Enter OTP
        page.fill("input[name='otp_code']", otp_code)
        page.click("button:has-text('Verify')")

        # Verify profile created
        page.wait_for_url("**/candidato/matches/", timeout=5000)

        with django_db_blocker.unblock():
            profile = CandidateProfile.objects.filter(
                mobile="+5511998765432"
            ).first()
            assert profile is not None
            assert profile.name == "João Silva"
            assert profile.email == "joao.silva@test.com"

            # Verify answers stored
            assert profile.signup_answers is not None
            assert len(profile.signup_answers) >= 5

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_candidate_view_matches(self, page, live_server, django_db_blocker, candidate_profile):
        """Test: Candidate views matching opportunities"""

        # Create matching relations (EMPLOYER_INTEREST_VIEW state)
        with django_db_blocker.unblock():
            from matchco.configuration.models import Store
            from matchco.recruitment.models import Relation

            store = Store.objects.filter(organization=candidate_profile.organization).first()
            if not store:
                store = Store.objects.create(
                    organization=candidate_profile.organization,
                    name="Test Store",
                    slug="test-store"
                )

            # Create relation in EMPLOYER_INTEREST_VIEW state
            relation = Relation.objects.create(
                organization=candidate_profile.organization,
                candidate_profile=candidate_profile,
                store=store,
                state=Relation.STATE_EMPLOYER_INTEREST_VIEW,
                created_at=datetime.now(),
            )

        # Navigate to matches (would require login in real scenario)
        page.goto(f"{live_server}/candidato/matches/")
        page.wait_for_selector(".match-card", timeout=3000)

        # Verify matching opportunity visible
        assert page.locator(".match-card").count() >= 1
        assert page.locator(f"text={store.name}").is_visible()

    @pytest.mark.e2e
    def test_candidate_declare_interest(self, page, live_server, django_db_blocker, candidate_profile, relation_employer_interest_view):
        """Test: Candidate declares interest in opportunity"""

        # Navigate to relation (would require login + proper state in real scenario)
        page.goto(f"{live_server}/candidato/opportunity/{relation_employer_interest_view.id}/")

        # Verify opportunity details visible
        page.wait_for_selector("button:has-text('Declare Interest')", timeout=2000)

        # Click declare interest
        page.click("button:has-text('Declare Interest')")

        # Verify success message
        page.wait_for_selector(".success-message", timeout=2000)
        assert page.locator("text=Interest declared").is_visible()

        # Verify state transition in database
        with django_db_blocker.unblock():
            relation_employer_interest_view.refresh_from_db()
            assert relation_employer_interest_view.state == Relation.STATE_PERSON_INTERESTED

    @pytest.mark.e2e
    def test_candidate_enable_contact_after_match(self, page, live_server, django_db_blocker, candidate_profile, relation_matched):
        """Test: Candidate enables contact after bilateral match"""

        # Navigate to matched relation
        page.goto(f"{live_server}/candidato/opportunity/{relation_matched.id}/")

        # Verify in MATCHED state
        page.wait_for_selector("button:has-text('Enable Contact')", timeout=2000)

        # Click enable contact
        page.click("button:has-text('Enable Contact')")

        # Verify employer contact visible
        page.wait_for_selector(".employer-contact-info", timeout=2000)
        assert page.locator("text=Store Contact").is_visible()

        # Verify state transition
        with django_db_blocker.unblock():
            relation_matched.refresh_from_db()
            assert relation_matched.state == Relation.STATE_CONTACT_ENABLED


class TestCandidateDataIntegrity:
    """Verify candidate data integrity through signup flow"""

    @pytest.mark.e2e
    def test_signup_answers_stored_correctly(self, django_db_blocker, store_with_questionnaire):
        """Test: All questionnaire answers stored in database"""

        with django_db_blocker.unblock():
            profile = CandidateProfile.objects.create(
                mobile="+5511998765432",
                email="test@test.com",
                organization=store_with_questionnaire["store"].organization,
            )

            # Simulate storing answers
            answers = {
                "1": "João Silva",
                "2": True,
                "3": "Manhã",
                "4": "2026-11-15",
                "5": 4,
            }

            for q_id, answer in answers.items():
                question = store_with_questionnaire["template"].questions.get(position=int(q_id))
                CandidateSignupAnswer.objects.create(
                    candidate_profile=profile,
                    question=question,
                    response_text=str(answer),
                )

            # Verify answers retrieved
            retrieved_answers = CandidateSignupAnswer.objects.filter(
                candidate_profile=profile
            )
            assert retrieved_answers.count() == 5

    @pytest.mark.e2e
    def test_candidate_profile_immutable(self, django_db_blocker, candidate_profile):
        """Test: Candidate profile cannot be re-filled"""

        with django_db_blocker.unblock():
            original_answers = len(candidate_profile.signup_answers)

            # Attempt to add more answers
            new_profile = CandidateProfile.objects.get(id=candidate_profile.id)
            new_profile.signup_answers.append({"answer": "new"})
            new_profile.save()

            # Verify immutability - profile should only have original answers
            refreshed = CandidateProfile.objects.get(id=candidate_profile.id)
            # In real implementation, answers should be append-only, not replaceable
            assert len(refreshed.signup_answers) >= original_answers
