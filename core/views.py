from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.tasks import ingest_customer_data, ingest_loan_data

# Create your views here.
@api_view(['POST'])
def ingest_data(request):
    try:
        ingest_customer_data.delay('data/customer_data.xlsx')
        ingest_loan_data.delay('data/loan_data.xlsx')
        return Response({"message": "Data ingestion started"}, status=202)
    except Exception as e:
        return Response({"error": str(e)}, status=500)