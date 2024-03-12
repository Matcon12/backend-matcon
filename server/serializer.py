from rest_framework import serializers
from .models import *

# class InvoiceForm(serializers.ModelSerializer):
#     class Meta:
#         model = Invoice
#         fields = '__all__'

class InwardDCForm(serializers.ModelSerializer):
    class Meta:
        model = InwDc
        fields = '__all__'

class CustomerMasterForm(serializers.ModelSerializer):
    class Meta:
        model = CustomerMaster
        fields = '__all__'

class PurchaseOrderForm(serializers.ModelSerializer):
    class Meta:
        model = Po
        fields = '__all__'

class PartMasterForm(serializers.ModelSerializer):
    class Meta:
        model = PartMaster
        fields = '__all__'

class MatCompaniesSerialize(serializers.ModelSerializer):
    class Meta:
        model = MatCompanies
        fields = '__all__'
        
class PartMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartMaster
        fields = ['id', 'part_name'] 
        
class POSerializer(serializers.ModelSerializer):
    class Meta:
        model = Po
        fields = ['po_date','cust_id', 'unit_price', 'part_id', 'uom']


class IPSerializer(serializers.ModelSerializer):
    class Meta:
        model = InwDc
        fields = ['part_name','unit_price', 'part_id']

class GstStatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = GstStates
        fields = ['state_code', 'state_name']
