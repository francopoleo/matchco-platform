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
        queryset = Company.objects.filter(organization_id__in=ids) if ids else Company.objects.none()
        queryset = self._get_filtered_queryset(queryset)
        return Response(CompanySerializer(queryset, many=True).data)


class GetBusinessUnitApi(HierarchyFilterMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        ids = request.query_params.getlist('ids')
        queryset = BusinessUnit.objects.filter(company_id__in=ids) if ids else BusinessUnit.objects.none()
        queryset = self._get_filtered_queryset(queryset)
        return Response(BusinessUnitSerializer(queryset, many=True).data)


class GetBusinessChannelApi(HierarchyFilterMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        ids = request.query_params.getlist('ids')
        queryset = BusinessChannel.objects.filter(company_id__in=ids) if ids else BusinessChannel.objects.none()
        queryset = self._get_filtered_queryset(queryset)
        return Response(BusinessChannelSerializer(queryset, many=True).data)


class GetOperationalUnitApi(HierarchyFilterMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        ids = request.query_params.getlist('ids')
        queryset = OperationalUnit.objects.filter(business_unit_id__in=ids) if ids else OperationalUnit.objects.none()
        queryset = self._get_filtered_queryset(queryset)
        return Response(OperationalUnitSerializer(queryset, many=True).data)


class GetJobFunctionApi(HierarchyFilterMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        ids = request.query_params.getlist('ids')
        company_ids = request.query_params.getlist('company_ids')
        if company_ids:
            queryset = JobFunction.objects.filter(company_id__in=company_ids)
        elif ids:
            queryset = JobFunction.objects.filter(channels__id__in=ids).distinct()
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
