from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from django.views.generic.edit import CreateView, UpdateView

from .models import Company, BusinessUnit, BusinessChannel, JobFunction, OperationalUnit, Organization


class HierarchyFilterMixin:
    """
    Mixin para filtrar por hierarquia ativa em APIs.
    Adiciona automaticamente active=True ao queryset.
    """
    filter_field = 'active'

    def _get_filtered_queryset(self, queryset):
        """Adiciona filtro active=True ao queryset"""
        if self.filter_field == 'active':
            return queryset.filter(active=True)
        return queryset

    def _active_organization_id(self, request):
        """APIs de hierarquia nunca aceitam IDs fora do tenant ativo."""
        organization = getattr(request, 'active_organization', None)
        return getattr(organization, 'pk', None)


class CompanySerializer(ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class BusinessUnitSerializer(ModelSerializer):
    class Meta:
        model = BusinessUnit
        fields = '__all__'


class OperationalUnitSerializer(ModelSerializer):
    class Meta:
        model = OperationalUnit
        fields = '__all__'


class BusinessChannelSerializer(ModelSerializer):
    class Meta:
        model = BusinessChannel
        fields = '__all__'


class JobFunctionSerializer(ModelSerializer):
    class Meta:
        model = JobFunction
        fields = '__all__'


class GetCompanyApi(HierarchyFilterMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        ids = request.query_params.getlist('ids')
        org_id = self._active_organization_id(request)
        queryset = Company.objects.filter(
            organization_id=org_id, pk__in=ids,
        ) if org_id and ids else Company.objects.none()
        queryset = self._get_filtered_queryset(queryset)
        return Response(CompanySerializer(queryset, many=True).data)


class GetBusinessUnitApi(HierarchyFilterMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        ids = request.query_params.getlist('ids')
        org_id = self._active_organization_id(request)
        queryset = BusinessUnit.objects.filter(
            company_id__in=ids, company__organization_id=org_id,
        ) if org_id and ids else BusinessUnit.objects.none()
        queryset = self._get_filtered_queryset(queryset)
        return Response(BusinessUnitSerializer(queryset, many=True).data)


class GetBusinessChannelApi(HierarchyFilterMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        ids = request.query_params.getlist('ids')
        org_id = self._active_organization_id(request)
        queryset = BusinessChannel.objects.filter(
            company_id__in=ids, company__organization_id=org_id,
        ) if org_id and ids else BusinessChannel.objects.none()
        queryset = self._get_filtered_queryset(queryset)
        return Response(BusinessChannelSerializer(queryset, many=True).data)


class GetOperationalUnitApi(HierarchyFilterMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        ids = request.query_params.getlist('ids')
        org_id = self._active_organization_id(request)
        queryset = OperationalUnit.objects.filter(
            business_unit_id__in=ids, business_unit__company__organization_id=org_id,
        ) if org_id and ids else OperationalUnit.objects.none()
        queryset = self._get_filtered_queryset(queryset)
        return Response(OperationalUnitSerializer(queryset, many=True).data)


class GetJobFunctionApi(HierarchyFilterMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        ids = request.query_params.getlist('ids')
        company_ids = request.query_params.getlist('company_ids')
        org_id = self._active_organization_id(request)
        if org_id and company_ids:
            queryset = JobFunction.objects.filter(
                company_id__in=company_ids, company__organization_id=org_id,
            )
        elif org_id and ids:
            queryset = JobFunction.objects.filter(
                channels__id__in=ids, company__organization_id=org_id,
            ).distinct()
        else:
            queryset = JobFunction.objects.none()
        queryset = self._get_filtered_queryset(queryset)
        return Response(JobFunctionSerializer(queryset, many=True).data)


class GetJobFunctionApiToUser(GetJobFunctionApi):
    pass


class CompanyCreateView(CreateView):
    model = Company
    fields = '__all__'


class CompanyEditView(UpdateView):
    model = Company
    fields = '__all__'
