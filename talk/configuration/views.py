from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from django.views.generic.edit import CreateView, UpdateView

from .models import Company, BusinessUnit, BusinessChannel, JobFunction, OperationalUnit, Organization


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


class GetCompanyApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        ids = request.query_params.getlist('ids')
        queryset = Company.objects.filter(organization_id__in=ids) if ids else Company.objects.none()
        return Response(CompanySerializer(queryset, many=True).data)


class GetBusinessUnitApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        ids = request.query_params.getlist('ids')
        queryset = BusinessUnit.objects.filter(company_id__in=ids) if ids else BusinessUnit.objects.none()
        return Response(BusinessUnitSerializer(queryset, many=True).data)


class GetBusinessChannelApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        ids = request.query_params.getlist('ids')
        queryset = BusinessChannel.objects.filter(company_id__in=ids) if ids else BusinessChannel.objects.none()
        return Response(BusinessChannelSerializer(queryset, many=True).data)


class GetOperationalUnitApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        ids = request.query_params.getlist('ids')
        queryset = OperationalUnit.objects.filter(business_unit_id__in=ids) if ids else OperationalUnit.objects.none()
        return Response(OperationalUnitSerializer(queryset, many=True).data)


class GetJobFunctionApi(APIView):
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
        return Response(JobFunctionSerializer(queryset, many=True).data)


class GetJobFunctionApiToUser(GetJobFunctionApi):
    pass


class CompanyCreateView(CreateView):
    model = Company
    fields = '__all__'


class CompanyEditView(UpdateView):
    model = Company
    fields = '__all__'
