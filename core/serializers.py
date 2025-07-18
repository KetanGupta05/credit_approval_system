from rest_framework import serializers
from .models import Customer, Loan

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class LoanSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)

    class Meta:
        model = Loan
        fields = '__all__'

class CustomerRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'age', 'monthly_income', 'phone_number']

    def create(self, validated_data):

        validated_data['credit_score'] = 650 
        score = validated_data['credit_score']
        income = validated_data['monthly_income']
        credit_limit = income * 0.36 if score >= 700 else income * 0.2

        validated_data['approved_limit'] = round(credit_limit, 2)

        return super().create(validated_data)
    

class CreateLoanSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Loan
        fields = ['customer_id', 'loan_amount', 'interest_rate', 'tenure', 'monthly_payment']

    def create(self, validated_data):
        customer_id = validated_data.pop('customer_id')
        customer = Customer.objects.get(id=customer_id)

        
        existing_emis = Loan.objects.filter(customer=customer).aggregate(total_emi=serializers.Sum('monthly_payment'))['total_emi'] or 0

        new_emi = validated_data['monthly_payment']
        if (existing_emis + new_emi) > customer.approved_limit:
            raise serializers.ValidationError("Loan rejected: EMI exceeds approved limit.")

        validated_data['customer'] = customer
        return Loan.objects.create(**validated_data)
