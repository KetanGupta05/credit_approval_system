import math
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from core.tasks import ingest_customer_data, ingest_loan_data
from .serializers import CustomerRegistrationSerializer, CreateLoanSerializer, LoanSerializer 
from .models import Customer, Loan

@api_view(['POST'])
def ingest_data(request):
    try:
        ingest_customer_data.delay('data/customer_data.xlsx')
        ingest_loan_data.delay('data/loan_data.xlsx')
        return Response({"message": "Data ingestion started"}, status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def register_customer(request):
    serializer = CustomerRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        customer = serializer.save()
        return Response({
            "message": "Customer registered successfully",
            "customer_id": customer.id,
            "approved_limit": customer.approved_limit,
            "credit_score": customer.credit_score
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def check_eligibility(request):
    try:
        customer_id = request.data.get("customer_id")
        loan_amount = float(request.data.get("loan_amount"))
        interest_rate = float(request.data.get("interest_rate"))
        tenure = int(request.data.get("tenure"))

        customer = Customer.objects.get(id=customer_id)

      
        R = interest_rate / 12 / 100
        N = tenure
        EMI = (loan_amount * R * math.pow(1 + R, N)) / (math.pow(1 + R, N) - 1)

        
        is_eligible = (customer.monthly_salary >= 2 * EMI) and (customer.approved_limit >= loan_amount)

        return Response({
            "customer_id": customer.id,
            "credit_score": customer.credit_score,
            "monthly_income": customer.monthly_salary,
            "approved_limit": customer.approved_limit,
            "approved": is_eligible,
            "message": "Customer is eligible for the loan" if is_eligible else "Customer is not eligible for the loan",
            "monthly_emi": round(EMI, 2),
            "interest_rate": interest_rate,
            "tenure": tenure
        }, status=status.HTTP_200_OK)

    except Customer.DoesNotExist:
        return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
def create_loan(request):
    serializer = CreateLoanSerializer(data=request.data)
    if serializer.is_valid():
        loan = serializer.save()
        return Response({"message": "Loan approved", "loan_id": loan.id}, status=201)
    return Response(serializer.errors, status=400)

@api_view(['GET'])
def view_loan(request, loan_id):
    try:
        loan = Loan.objects.get(pk=loan_id)
    except Loan.DoesNotExist:
        return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = LoanSerializer(loan)
    return Response(serializer.data)


@api_view(['GET'])
def view_loans(request, customer_id):
    try:
        customer = Customer.objects.get(pk=customer_id)
        loans = Loan.objects.filter(customer=customer)
        serializer = LoanSerializer(loans, many=True)
        return Response(serializer.data)
    except Customer.DoesNotExist:
        return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)