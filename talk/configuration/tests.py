from django.test import TestCase
from configuration.models import Organization, Company, BusinessUnit, BusinessChannel


class EpsonTestCase(TestCase):

    def setUp(self):
        self.organization = Organization.objects.create(name='Sandra', slug='sandra')
        self.company = Company.objects.create(name='Company', organization=self.organization)
        self.business_unit = BusinessUnit.objects.create(name='Unit', company=self.company)
        self.channel = BusinessChannel.objects.create(name='Retail', company=self.company)

    def test_unit(self):
        self.organization.name = 'Sandra Updated'
        self.organization.save()
        self.assertEqual(self.organization.name, 'Sandra Updated')

    def test_channel(self):
        self.channel = BusinessChannel.objects.all()
        self.assertEqual(len(self.channel), 1)

    def test_company(self):
        company = Company.objects.all()
        self.assertEqual(len(company), 1)

    def test_companyUnit(self):
        business_units = BusinessUnit.objects.all()
        self.assertEqual(len(business_units), 1)
