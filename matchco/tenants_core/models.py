"""
Modelos Espelho para Isolamento de Dados em Schemas Tenant

Estes modelos espelham dados de SHARED_APPS no schema público,
permitindo ForeignKeys seguras dentro do schema tenant.

Sincronização: Feita via signals em configuration/signals.py
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class TenantUser(models.Model):
    """
    Espelho de auth.User no schema tenant.

    Permite que modelos tenant tenham FK para usuários sem
    referenciar schema público.

    Sincronizado automaticamente quando User muda em schema público.
    """
    user_id = models.IntegerField(primary_key=True)
    username = models.CharField(_('Username'), max_length=150)
    email = models.EmailField(_('Email'), max_length=254)
    first_name = models.CharField(_('First Name'), max_length=150, blank=True)
    last_name = models.CharField(_('Last Name'), max_length=150, blank=True)
    is_active = models.BooleanField(_('Is Active'), default=True)

    class Meta:
        managed = True
        verbose_name = _('Tenant User')
        verbose_name_plural = _('Tenant Users')

    def __str__(self):
        return f"{self.username} (ID: {self.user_id})"


class TenantOrganization(models.Model):
    """
    Espelho de configuration.Organization no schema tenant.

    Permite que modelos tenant tenham FK para organização sem
    referenciar schema público.

    Sincronizado automaticamente quando Organization muda.
    """
    organization_id = models.IntegerField(primary_key=True)
    name = models.CharField(_('Name'), max_length=160)
    slug = models.SlugField(_('Slug'), max_length=180)

    class Meta:
        managed = True
        verbose_name = _('Tenant Organization')
        verbose_name_plural = _('Tenant Organizations')

    def __str__(self):
        return f"{self.name} (ID: {self.organization_id})"


class TenantCompany(models.Model):
    """
    Espelho de configuration.Company no schema tenant.

    Permite que modelos tenant tenham FK para company sem
    referenciar schema público.

    Sincronizado automaticamente quando Company muda.
    """
    company_id = models.IntegerField(primary_key=True)
    name = models.CharField(_('Name'), max_length=160)

    class Meta:
        managed = True
        verbose_name = _('Tenant Company')
        verbose_name_plural = _('Tenant Companies')

    def __str__(self):
        return f"{self.name} (ID: {self.company_id})"
