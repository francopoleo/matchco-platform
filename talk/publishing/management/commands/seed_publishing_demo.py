from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from publishing.models import Publication, Tag
from configuration.models import Organization, Company, BusinessUnit, OperationalUnit, Membership


class Command(BaseCommand):
    help = 'Create repeatable demo Feed and Wiki publications with images and tags.'

    def handle(self, *args, **options):
        User = get_user_model()
        author = User.objects.filter(is_superuser=True).first() or User.objects.order_by('id').first()
        if author is None:
            self.stderr.write('No user exists to author the demo publications.')
            return

        organization, _ = Organization.objects.get_or_create(slug='talk-learning', defaults={'name': 'Talk Learning'})
        company, _ = Company.objects.get_or_create(organization=organization, name='Demo Enterprise')
        business_unit, _ = BusinessUnit.objects.get_or_create(company=company, name='Learning Operations')
        operational_unit, _ = OperationalUnit.objects.get_or_create(
            business_unit=business_unit, name='Learning Campus'
        )
        Membership.objects.get_or_create(
            user=author, organization=organization, company=company,
            business_unit=business_unit, operational_unit=operational_unit,
            defaults={'is_primary': True},
        )

        tags = {slug: Tag.objects.get_or_create(slug=slug, defaults={'name': name})[0] for slug, name in {
            'learning': 'Learning', 'technology': 'Technology', 'security': 'Security', 'cloud': 'Cloud', 'networking': 'Networking',
        }.items()}
        publications = [
            ('demo-feed-new-learning-path', 'feed', 'New learning path available', 'A new learning path is available in Talk Learning. Start with the fundamentals and continue at your own pace.', 'A new learning path is available in Talk Learning. Explore the Network Fundamentals course and build your next skill.', 'images/Banners-Feed-Wiki-01.max-800x600.png', ['learning', 'networking']),
            ('demo-feed-security-update', 'feed', 'Security update: protect your accounts', 'A quick reminder about practical security habits for your daily work.', 'Use strong passwords, enable multifactor authentication and report anything suspicious to the security team.', 'images/technology-innovation-photo.max-165x165.jpg', ['security', 'learning']),
            ('demo-wiki-networking-basics', 'wiki', 'Networking basics', 'A permanent reference for the concepts behind modern networks.', 'Use this article as a reference for IP addresses, DNS, routing and the most common connectivity checks. Revisit it whenever you need a quick explanation or a starting point for deeper study.', 'images/Redes.max-800x600.jpg', ['networking', 'technology']),
            ('demo-wiki-cloud-glossary', 'wiki', 'Cloud glossary', 'A practical glossary of cloud and infrastructure terms.', 'This reference explains the most common cloud concepts, including regions, availability zones, managed services, scalability and observability. Keep it close while studying the Cloud Foundations course.', 'images/nuvem-computacao.width-800.jpg', ['cloud', 'technology']),
        ]
        for slug, kind, title, excerpt, body, image, tag_slugs in publications:
            publication, _ = Publication.objects.update_or_create(slug=slug, defaults={'kind': kind, 'organization': organization, 'title': title, 'excerpt': excerpt, 'body': body, 'image': image, 'author': author, 'status': Publication.PUBLISHED, 'published_at': timezone.now()})
            publication.tags.set([tags[tag_slug] for tag_slug in tag_slugs])
            self.stdout.write(self.style.SUCCESS(f'{kind.title()} ready: {publication.title}'))
