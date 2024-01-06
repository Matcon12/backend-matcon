import sys ,os
import openpyxl
from dateutil.parser import parse
from django.shortcuts import redirect, render,HttpResponse
from rest_framework import status
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.db.models import Sum
from .models import *
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.parsers import JSONParser
from django.shortcuts import render 
from rest_framework.views import APIView 
from . models import *
from rest_framework.response import Response 
from . serializer import *
import datetime as d
from datetime import datetime
#pip3 install Babel
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
from django.contrib.auth import authenticate, login,logout
import json
from django.shortcuts import render
from django.db.models import Sum
import pandas as pd
from .models import OtwDc
from django.db.models import F, ExpressionWrapper, DateTimeField
from django.db.models.functions import Cast
from django.utils.timezone import make_aware
from django.views import View

from babel.numbers import format_currency



def report(request):
    return render(request,'reports.html')



@login_required(login_url='login')
def HomePage(req):
    return render(req,'home.html')


class SignUpPage(APIView):
    def post(self,req):
        data = req.data
        print(data)
        uname = data['uname']
        pass1 = data['pass1']
        pass2 = data['pass2']

        if pass1 != pass2:
            return Response(status=status.HTTP_400_BAD_REQUEST,data ={'pw': pass1})
        else :
            try:
                user = User.objects.get(username=uname)
                return Response(status=status.HTTP_400_BAD_REQUEST, data = {'username' : data['uname']})
            except:
                my_user = User.objects.create_user(username= uname)
                my_user.set_password(pass1)
                my_user.save()
          
        
        return Response(status=status.HTTP_202_ACCEPTED)

class LoginPage(APIView):
    def post(self,req):
        data = req.data
        print(data)
        username = data['uname']
        password = data['password']
        user = authenticate(username=username,password =password)
        print(user)
        if user is not None:
            login(req,user)
            return Response(status=status.HTTP_200_OK,data='successful')
            # return redirect('home')
        else:
            return Response(status = status.HTTP_200_OK,data = 'incorrect')
       

class LogoutPage(APIView):
    def post(self,req):
        logout(req)
        return Response(status = status.HTTP_200_OK,data = 'out')


class InvoicePrint(APIView):
    def get(self, request):
        print("get request recevied")
        try:
            data = invoice_print(request)
            # print(data, 'data before sending to frontend')
            if data == 'invalid otw_dc_no':
                return HttpResponse('Invalid otw_dc')
            return render(request, 'tax_invoice.html', data)
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)

class DCPrint(APIView):
    def get(self, request):
        try:
            data = dc_print(request)
            if data == 'invalid otw_dc_no':
                return HttpResponse('Invalid otw_dc')
            return render(request, 'dc.html', data)
            # return Response(data=data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    
def convert_rupees_to_words(amount):
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", 
            "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen","Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    thousands = ["", "Thousand", "Lakh", "Crore"]
    def convert_two_digits(num):
        if num < 20:
            return ones[num] + " "
        else:
            return tens[num // 10] + " " + ones[num % 10]
    def convert_three_digits(num):
        if num < 100:
            return convert_two_digits(num)
        else:
            return ones[num // 100] + " Hundred " + convert_two_digits(num % 100)
    result = ""    
    amount = format(amount, ".2f")
    # print(type(amount))   
    RsPs = str(amount).split('.')
    Rs = int(RsPs[0])
    Ps = int(RsPs[1])
    if Rs == 0:
        result += "Zero "
    else:
        for i in range(4):
            if i == 0 or i == 3:
                chunk = Rs % 1000
                Rs //= 1000
            else:
                chunk = Rs % 100
                Rs //= 100
            if chunk != 0:
                result = convert_three_digits(chunk) + " " + thousands[i] + " " +result
    if Ps > 0:
        result = result.strip() + " and Paise " + convert_two_digits(Ps)        
    result = "Rupees " + result.strip() + " Only"
    # print("conversion success")
    return result.upper()

class InvoiceProcessing(APIView):    
    def post(self, request):
        try:
            print("entering try block for invoice processing")
            response_data = invoice_processing(request)
            print("Response from invoice processing:", response_data)

            if response_data == 'Nothing to be delivered':
                print("Nothing to be delivered")
                return Response(status=status.HTTP_200_OK, data='zero items')
            
            elif response_data == 'grn_no does not exists':
                print("grn_no does not exists")
                return Response(status=status.HTTP_200_OK, data='grn_no')
            
            elif 'message' in response_data and 'gcn_no' in response_data:
                print("success")
                gcn_no = response_data['gcn_no']
                return Response(status=status.HTTP_200_OK, data={'message': 'success', 'gcn_no': gcn_no})
            
            elif response_data == 'open_po_validity':
                print("open_po_validity")
                return Response(status=status.HTTP_200_OK, data='open_po')
            
            elif response_data[0:8] == 'po_sl_no':
               return Response(status=status.HTTP_200_OK,data = response_data)
            
            else:
                return Response(status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)

class GetPartNameView(APIView):
    def get(self, request, part_id, cust_id):
        print("Entering API class")
        part = get_object_or_404(PartMaster, part_id=part_id, cust_id=cust_id)
        serializer = PartMasterSerializer(part)
        return Response({'part_name': serializer.data['part_name']})


class GetINWDetailsView(APIView):
    def get(self, request, grn_no):
        print("Entering API class")
        part = get_object_or_404(InwDc, grn_no=grn_no)
        serializer = InwardDCForm(part)
        response_data = {
            'grn_date': serializer.data['grn_date'],
            'po_no': part.po_no,  
            'cust_id': part.cust_id, 
            'po_date':part.po_date, 
        }
        return Response (response_data)


class GetPOSlNoDetailsView(APIView):
       def get(self, request, po_no, part_id):
        try:
            print("enetring try block")
            data=get_object_or_404(Po, po_no=po_no,part_id=part_id)
            serializer =PurchaseOrderForm(data)
            response_data={
                'po_sl_no': serializer.data['po_sl_no'],
                'qty': serializer.data['qty'],
                'unit_price': serializer.data['unit_price'],
            }
            return Response(response_data)
        except Po.DoesNotExist:
            return Response({'error': 'PO not found'}, status=404) 
        
class GetPOSlNo(APIView):
       def get(self, request, po_no, po_sl_no):
        try:
            print("enetring try block to get po sl no ")
            data=get_object_or_404(Po, po_no=po_no,po_sl_no=po_sl_no)
            serializer =PurchaseOrderForm(data)
            response_data={
                'part_id': serializer.data['part_id'],
                'qty': serializer.data['qty'],
                'unit_price': serializer.data['unit_price'],
            }
            return Response(response_data)
        except Po.DoesNotExist:
            return Response({'error': 'PO not found'}, status=404)         


class GetPOSlNoInw(APIView):
    def get(self, request, grn_no, po_sl_no):
        try:
            print("Entering try block to get po sl no ")
            data = get_object_or_404(InwDc, grn_no=grn_no, po_sl_no=po_sl_no)
            serializer = InwardDCForm(data)
            response_data = {
                'part_id': serializer.data['part_id'],
                'qty_received': serializer.data['qty_received'],
                'unit_price': serializer.data['unit_price'],
            }
            return Response(response_data)
        except InwDc.DoesNotExist:
            return Response({'error': 'Inw DC not found'}, status=404)

class GetPOSlNoDetailsInwView(APIView):
    def get(self, request, grn_no, part_id):
        try:
            print("enetring try block to get info for po sl no")
            data=get_object_or_404(InwDc, grn_no=grn_no,part_id=part_id)
            print(data,"data")
            serializer =InwardDCForm(data)
            response_data={
                'po_sl_no': serializer.data['po_sl_no'],
                'qty_received': serializer.data['qty_received'],
                'unit_price': serializer.data['unit_price'],
            }
            return Response(response_data)
        except InwDc.DoesNotExist:
            return Response({'error': 'Inward DC not found'}, status=404)  
        
    

        
class GetPODetailsView(APIView):
    def get(self, request, po_no):
        try:
            po_instance = Po.objects.filter(po_no=po_no).first()
            print(po_instance,"po no")

            if po_instance:
                serializer = PurchaseOrderForm(po_instance)
                print(serializer,"serializer")
                response_data={
                'po_date': serializer.data['po_date'],
                'cust_id': serializer.data['cust_id'],
                }
                print("po data",response_data)
                return Response(response_data)
            else:
                return Response({'error': 'PO not found'}, status=404)
        except Exception as e:
            return Response({'error': 'Internal Server Error'}, status=500)

   
class GetInfoView(APIView):
       def get(self, request, po_no,po_sl_no):
        try:
            print("enetring try block to get info")
            po_instance =get_object_or_404(Po,po_no=po_no,po_sl_no=po_sl_no)
            serializer =PurchaseOrderForm(po_instance)
            return Response({
                'part_id': serializer.data['part_id'],
                'unit_price': serializer.data['unit_price'],
                'uom': serializer.data['uom'],
            })
        except Po.DoesNotExist:
            return Response({'error': 'PO not found'}, status=404)    
        
class GetIPDetailsView(APIView):
       def get(self, request, grn_no,po_sl_no):
        try:
            print("entering try block to get info for invoice processing")
            ip =get_object_or_404(InwDc,grn_no=grn_no,po_sl_no=po_sl_no)
            serializer =IPSerializer(ip)
            return Response({
                'part_id': serializer.data['part_id'],
                'unit_price': serializer.data['unit_price'],
                'part_name': serializer.data['part_name'],
            })
        except InwDc.DoesNotExist:
            return Response({'error': 'Inward DC not found'}, status=404)   

    
class GetCN(APIView):
    def get(self, request,cust_id):
        print("Entering API class")
        part = get_object_or_404(CustomerMaster, cust_id=cust_id)
        serializer = CustomerMasterForm(part)
        return Response({'cust_name': serializer.data['cust_name']})
    
    
class InwardDcInput(APIView): 
    def post(self, request):
        request.data['qty_delivered'] = 0
        request.data['qty_balance'] = request.data['qty_received']
        serializer = InwardDCForm(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # print('saved to database')
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerMasterInput(APIView):
    def post(self, request):
        serializer = CustomerMasterForm(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PartMasterInput(APIView):
    def post(self, request):
        serializer = PartMasterForm(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PurchaseOrderInput(APIView):
    def post(self, request):
        request.data['qty_sent'] = 0
        serializer = PurchaseOrderForm(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    

import os
class InvoiceReport(APIView):
    def post(self, request):
        print("post request ")
        try:
            data = invoice_report(request)
            print(data, "data values")
            if data is not None:
                return Response({'message': 'Invoice report generated successfully', 'data': data}, status=status.HTTP_200_OK)
            
            return Response({'error': 'No data available'}, status=status.HTTP_404_NOT_FOUND)
           

        except Exception as e:
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
    

def invoice_processing(request):
    grn_no = request.data['grn_no']
    mat_code = request.data['mcc']
    query_set = InwDc.objects.filter(grn_no=grn_no)
    print(len(query_set))

    if request.data['rejected'] == 1:
        ritem = 1
    else:
        ritem = 0 

    try:
        if query_set.exists():
            query = query_set[0]
            po_sl_numbers = []
            for i in range(int(request.data['items'])):
                item = 'item'+str(i)
                po_sl_no = int(request.data[item]['po_sl_no'])
                qty_to_be_delivered = int(request.data[item]['qty_delivered'])
                po_sl_numbers.append(po_sl_no)

                try :
                    po_sl_no = get_object_or_404(InwDc, grn_no=grn_no, po_sl_no=po_sl_no).po_sl_no
                
                    balance_qty = query.qty_balance
                    qty_received = query.qty_received
                    po_no = query.po_no
                    qty = get_object_or_404(Po, po_no=po_no, po_sl_no=po_sl_no).qty
                    qty_sent = get_object_or_404(Po, po_no=po_no, po_sl_no=po_sl_no).qty_sent
                    rework_dc = query.rework_dc
                    grn_date = query.grn_date
                    qty_to_be_updated_in_po=qty_to_be_delivered+qty_sent
                    open_po = get_object_or_404(Po, po_no=po_no, po_sl_no=po_sl_no).open_po
                    open_po_validity = get_object_or_404(Po, po_no=po_no, po_sl_no=po_sl_no).open_po_validity

                    if qty_to_be_delivered <= balance_qty and qty_to_be_delivered<=qty_received:
                        InwDc.objects.filter(grn_no=grn_no, po_sl_no=po_sl_no).update(qty_delivered=models.F('qty_delivered') + qty_to_be_delivered)

                        InwDc.objects.filter(grn_no=grn_no, po_sl_no=po_sl_no).update(qty_balance=models.F('qty_balance') - qty_to_be_delivered)

                        
                        if rework_dc==True:
                            print('pass')
                            pass
                        else:
                            if qty_to_be_updated_in_po <= qty or open_po==True:
                                print("Before update - qty_sent:", get_object_or_404(Po, po_no=po_no, po_sl_no=po_sl_no).qty_sent)
                                Po.objects.filter(po_no=po_no, po_sl_no=po_sl_no).update(qty_sent=models.F('qty_sent') + qty_to_be_delivered)
                                print("After update - qty_sent:", get_object_or_404(Po, po_no=po_no, po_sl_no=po_sl_no).qty_sent)
                            else:
                                print("Sorry , there is nothing to be delivered ")
                                sys.exit()
                        
                        if open_po==True:
                            if grn_date > open_po_validity:
                                return 'open_po_validity'

                        balance_qty = get_object_or_404(InwDc, grn_no=grn_no, po_sl_no=po_sl_no).qty_balance
                        updated_qty_delivered = get_object_or_404(InwDc, grn_no=grn_no, po_sl_no=po_sl_no).qty_delivered
                        print("Remaining qty : \n", balance_qty)
                        print("Updated delivered qtuantities : \n", updated_qty_delivered)

                    else:
                        return "Nothing to be delivered"
                
                except Exception as e:
                    print('type' ,e)
                    print(f"The part item with '{po_sl_no}' does not exist in the database.") 
                    return "po_sl_no" + str(po_sl_no)
            
            current= d.datetime.now()
            print(current,"current value ")
            current_yyyy = current.year
            current_mm = current.month
            fin_year = int(get_object_or_404(MatCompanies, mat_code=mat_code).fin_yr)
            print(type(fin_year))

            if  fin_year < current_yyyy and current_mm >3:
                fin_year=current_yyyy
                MatCompanies.objects.filter(mat_code=mat_code).update(fin_yr=fin_year)
            f_year=fin_year+1
            fy=str(f_year)
            fyear=fy[2:]

            gcn_no = get_object_or_404(MatCompanies,mat_code='MEE').last_gcn_no
            print("Source Value:", gcn_no)
            destination_value = gcn_no + 1
            print("Destination Value:", destination_value)
            MatCompanies.objects.filter(mat_code='MEE').update(last_gcn_no = destination_value)
            if rework_dc==True:
                flag='R'
            else:
                flag=''    
            gcn_num=(str(destination_value).zfill(3)  + flag+ "/" + str(fin_year)+"-"+str(fyear))
           
            current_date = current
            date = str(current_date.strftime('%Y-%m-%d'))
            
            data_inw = InwDc.objects.filter(grn_no=grn_no, po_sl_no__in=po_sl_numbers).values('grn_no', 'grn_date', 'po_no', 'po_date', 'receiver_id', 'consignee_id', 'po_sl_no', 'part_id', 'qty_delivered', 'uom', 'unit_price', 'part_name') 
            code='MEE'
            
            rows = InwDc.objects.filter(grn_no=grn_no).values('qty_delivered', 'unit_price')
            list_tax_amt=[]
            total_taxable_amount = 0
            
            for row in rows:
                qty_delivered, unit_price = row['qty_delivered'], row['unit_price']
                taxable_amount = qty_delivered * unit_price
                formatted_number = float('{:.2f}'.format(taxable_amount))

                list_tax_amt.append(formatted_number)
                # print(taxable_amount)
                total_taxable_amount += formatted_number
            print("Total Taxable Amount:", total_taxable_amount)  
            
            
            insert_data = []
            for idx, row in enumerate(data_inw):
                x=po_no
                print(x)
                receiver_id = Po.objects.filter(po_no=x).values_list('receiver_id', flat=True).first()
                state_code = CustomerMaster.objects.filter(cust_id=receiver_id).values_list('cust_st_code', flat=True).first()
                print(state_code)

                if ritem == 1:
                    amt = 0
                else:
                    amt = list_tax_amt[idx]

                if state_code == 29:
                    cgst_price = '{:.2f}'.format( 0.09 * amt)
                    sgst_price = '{:.2f}'.format( 0.09 * amt)
                    igst_price = 0   
                else:
                    cgst_price = 0  
                    sgst_price = 0  
                    igst_price = '{:.2f}'.format( 0.18 * amt)
                    
                try:
                  receiver_instance = CustomerMaster.objects.get(cust_id=row.get('receiver_id'))
                except CustomerMaster.DoesNotExist:
                  print(f"Receiver with id {row.get('receiver_id')} does not exist.")
                  continue
                    
                insert_instance = OtwDc(
                    mat_code=code,
                    gcn_no=gcn_num,
                    gcn_date=date,
                    grn_no=row['grn_no'],
                    grn_date=row['grn_date'],
                    po_no=row['po_no'],
                    po_date=row['po_date'],
                    receiver_id=receiver_instance,
                    consignee_id=row['consignee_id'],
                    po_sl_no=row['po_sl_no'],
                    part_id=row['part_id'],
                    qty_delivered=row['qty_delivered'],
                    uom=row['uom'],
                    unit_price=row['unit_price'],
                    part_name=row['part_name'],
                    taxable_amt=amt,
                    cgst_price=cgst_price,
                    sgst_price=sgst_price,
                    igst_price=igst_price,
                    rejected_item=ritem
                    )

                insert_data.append(insert_instance) 
                    
            OtwDc.objects.bulk_create(insert_data) 
            response_data = {
            'message': 'success',
            'gcn_no': gcn_num,
                   }
            print(type(response_data))
            return response_data 
        else:
            print(f"The record with '{grn_no}' does not exist in the database.")
            return('grn_no does not exists')
            
    except Exception as e:
        print(e)

def invoice_print(request):
    try:
        gcn_no = request.query_params.get('data[gcn_no]')
        print(gcn_no)
        odc = OtwDc.objects.filter(gcn_no=gcn_no)
        odc1=OtwDc.objects.filter(gcn_no=gcn_no)[0] 
        mat = odc1.mat_code
        m = MatCompanies.objects.get(mat_code=mat)
        r_id = odc1.receiver_id.cust_id
        r = CustomerMaster.objects.get(cust_id=r_id)
        c_id = odc1.consignee_id
        c = CustomerMaster.objects.get(cust_id=c_id)
        gr = get_object_or_404(GstRates,id=1)
        total_qty = OtwDc.objects.filter(gcn_no=gcn_no).aggregate(total_qty=Sum('qty_delivered'))['total_qty']
        total_taxable_value =OtwDc.objects.filter(gcn_no=gcn_no).aggregate(total_taxable_value=Sum('taxable_amt'))['total_taxable_value']
        total_cgst = OtwDc.objects.filter(gcn_no=gcn_no).aggregate(total_cgst=Sum('cgst_price'))['total_cgst']
        total_sgst = OtwDc.objects.filter(gcn_no=gcn_no).aggregate(total_sgst=Sum('sgst_price'))['total_sgst']
        total_igst = OtwDc.objects.filter(gcn_no=gcn_no).aggregate(total_igst=Sum('igst_price'))['total_igst']
        grand_total= round(float('{:.2f}'.format(total_taxable_value+total_cgst+total_sgst+total_igst)))
        gt=format_currency(grand_total, 'INR', locale='en_IN')
        aw = convert_rupees_to_words(grand_total) 
        context = {
            'odc': odc,
            'm': m,
            'r': r,
            'c': c,
            'gr': gr,
            'odc1': odc1,
            'amount' : aw,
            'total_taxable_value':"{:.2f}".format(total_taxable_value),
            'total_cgst':"{:.2f}".format(total_cgst),
            'total_sgst':"{:.2f}".format(total_sgst),
            'total_igst':"{:.2f}".format(total_igst),
            'gt':gt,
            'total_qty':total_qty,  
        }
        return context
    except Exception as e:
        print(e)
        return "invalid otw_dc_no"


def dc_print(request):
    try:
        gcn_no=request.query_params.get('data[gcn_no]')
        odc=OtwDc.objects.filter(gcn_no=gcn_no)
        odc1=OtwDc.objects.filter(gcn_no=gcn_no)[0]
        c_id=odc1.consignee_id
        c=CustomerMaster.objects.get(cust_id=c_id)
        r_id = odc1.receiver_id.cust_id
        r = CustomerMaster.objects.get(cust_id=r_id)
        mat= odc1.mat_code
        m=MatCompanies.objects.get(mat_code=mat)
        context = {
            'm':m,
            'c':c,
            'r':r,
            'odc1':odc1,
            'odc':odc,
        
        }
        return context
    
    except Exception as e:
        print(e)
        return "invalid otw_dc_no"
def invoice_print(request):
    try:
        gcn_no = request.query_params.get('data[gcn_no]')
        print(gcn_no)
        odc = OtwDc.objects.filter(gcn_no=gcn_no)
        odc1=OtwDc.objects.filter(gcn_no=gcn_no)[0] 
        mat = odc1.mat_code
        m = MatCompanies.objects.get(mat_code=mat)
        r_id = odc1.receiver_id.cust_id
        r = CustomerMaster.objects.get(cust_id=r_id)
        c_id = odc1.consignee_id
        c = CustomerMaster.objects.get(cust_id=c_id)
        gr = get_object_or_404(GstRates,id=1)
        total_qty = OtwDc.objects.filter(gcn_no=gcn_no).aggregate(total_qty=Sum('qty_delivered'))['total_qty']
        total_taxable_value =OtwDc.objects.filter(gcn_no=gcn_no).aggregate(total_taxable_value=Sum('taxable_amt'))['total_taxable_value']
        total_cgst = OtwDc.objects.filter(gcn_no=gcn_no).aggregate(total_cgst=Sum('cgst_price'))['total_cgst']
        total_sgst = OtwDc.objects.filter(gcn_no=gcn_no).aggregate(total_sgst=Sum('sgst_price'))['total_sgst']
        total_igst = OtwDc.objects.filter(gcn_no=gcn_no).aggregate(total_igst=Sum('igst_price'))['total_igst']
        grand_total= round(float('{:.2f}'.format(total_taxable_value+total_cgst+total_sgst+total_igst)))
        gt=format_currency(grand_total, 'INR', locale='en_IN')
        aw = convert_rupees_to_words(grand_total) 
        context = {
            'odc': odc,
            'm': m,
            'r': r,
            'c': c,
            'gr': gr,
            'odc1': odc1,
            'amount' : aw,
            'total_taxable_value':"{:.2f}".format(total_taxable_value),
            'total_cgst':"{:.2f}".format(total_cgst),
            'total_sgst':"{:.2f}".format(total_sgst),
            'total_igst':"{:.2f}".format(total_igst),
            'gt':gt,
            'total_qty':total_qty,  
        }
        return context
    except Exception as e:
        print(e)
        return "invalid otw_dc_no"


def dc_print(request):
    try:
        gcn_no=request.query_params.get('data[gcn_no]')
        odc=OtwDc.objects.filter(gcn_no=gcn_no)
        odc1=OtwDc.objects.filter(gcn_no=gcn_no)[0]
        c_id=odc1.consignee_id
        c=CustomerMaster.objects.get(cust_id=c_id)
        r_id = odc1.receiver_id.cust_id
        r = CustomerMaster.objects.get(cust_id=r_id)
        mat= odc1.mat_code
        m=MatCompanies.objects.get(mat_code=mat)
        context = {
            'm':m,
            'c':c,
            'r':r,
            'odc1':odc1,
            'odc':odc,
        
        }
        return context
    
    except Exception as e:
        print(e)
        return "invalid otw_dc_no"
    
from django.views.decorators.csrf import csrf_exempt   
@csrf_exempt   
def invoice_report(request):
 
 if request.method == 'POST':
  try:  
    data = json.loads(request.body)
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    print(f"Start Date: {start_date_str}, End Date: {end_date_str}")
    start_datetime = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_datetime = datetime.strptime(end_date_str, "%Y-%m-%d")
    start_date=start_datetime.date()
    end_date=end_datetime.date()
   
    result = OtwDc.objects.filter(
    gcn_date__range=(start_date, end_date)
    ).select_related('receiver_id').values(
    'gcn_no', 'gcn_date', 'qty_delivered', 'taxable_amt', 'cgst_price', 'sgst_price', 'igst_price',
    'receiver_id__cust_name', 'receiver_id__cust_gst_id',
    ).order_by('gcn_date')
    
    print(str(result.query))
    
 
    df = pd.DataFrame(result, columns=['gcn_no', 'gcn_date', 'qty_delivered', 'taxable_amt', 'cgst_price', 'sgst_price', 'igst_price', 'receiver_id__cust_name', 'receiver_id__cust_gst_id'])
    df = df[['receiver_id__cust_name', 'receiver_id__cust_gst_id', 'gcn_no', 'gcn_date', 'qty_delivered', 'taxable_amt', 'cgst_price', 'sgst_price', 'igst_price']]
    df.insert(0, 'Sl No', range(1, len(df) + 1))
    df['HSN/SSC'] = 9988
    df = df.rename(columns={
            'gcn_no': 'Invoice Number',
            'gcn_date': 'Invoice Date',
            'qty_delivered': 'Quantity',
            'taxable_amt': 'Ass.Value',
            'cgst_price': 'CGST Price (9%)',
            'sgst_price': 'SGST Price (9%)',
            'igst_price': 'IGST Price (18%)',
            'receiver_id__cust_name': 'Customer Name',
            'receiver_id__cust_gst_id': 'Customer GST Num',
        })
    df1 = df[['Customer Name', 'Customer GST Num']].copy()

    grouped = df.groupby(['Invoice Number','Invoice Date']).agg({
            'Quantity': 'sum',
            'Ass.Value': 'sum',
            'CGST Price (9%)': 'sum',
            'SGST Price (9%)': 'sum',
            'IGST Price (18%)': 'sum'
        }).reset_index()
   
    
    df1 = df[['Invoice Number', 'Customer Name', 'Customer GST Num']].drop_duplicates()
    df1['HSN/SSC'] = 9988
   
    combined_df = pd.merge(df1, grouped, on='Invoice Number', how='left')
    combined_df['Sl No'] = range(1, len(combined_df) + 1)
    
    total_taxable_amt = grouped['Ass.Value'].sum()
    total_cgst_price = grouped['CGST Price (9%)'].sum()
    total_sgst_price = grouped['SGST Price (9%)'].sum()
    total_igst_price = grouped['IGST Price (18%)'].sum()
    combined_df['Invoice Date'] = pd.to_datetime(combined_df['Invoice Date'], errors='coerce').dt.date
    combined_df['Invoice Date']=pd.to_datetime(combined_df['Invoice Date'], format='%Y-%m-%d').dt.strftime('%d-%m-%Y')
    combined_df['Invoice Date']=combined_df['Invoice Date'].astype(str)


    total_row = pd.DataFrame({
            'Sl No': 'Total',
            'Customer Name': '',
            'Customer GST Num': '',
            'Invoice Date': '',
            'Invoice Number': '',
            'Quantity': '',
            'Ass.Value': total_taxable_amt,
            'CGST Price (9%)': total_cgst_price,
            'SGST Price (9%)': total_sgst_price,
            'IGST Price (18%)': total_igst_price,
            'HSN/SSC': '',
            'Round Off':'',
        }, index=[0])
     

    combined_df = pd.concat([combined_df, total_row], ignore_index=True)
    

    combined_df['HSN/SSC'] = combined_df['HSN/SSC'].iloc[:-1].where(combined_df['Sl No'] != len(combined_df), 9988)
   
    combined_df['Invoice Value'] = combined_df['Ass.Value'] + combined_df['IGST Price (18%)'] + combined_df['CGST Price (9%)'] + combined_df['SGST Price (9%)']

    combined_df['Invoice Value'] = pd.to_numeric(combined_df['Invoice Value']).round()
    
    combined_df['Round Off'] = combined_df.apply(
     lambda row: float(row['Invoice Value']) - (
        float(row['Ass.Value']) +
        float(row['IGST Price (18%)']) +
        float(row['CGST Price (9%)']) +
        float(row['SGST Price (9%)'])
     ) if row['Sl No'] != 'Total' else None,
     axis=1
     )
    
    combined_df[['Ass.Value', 'IGST Price (18%)', 'CGST Price (9%)', 'SGST Price (9%)', 'Invoice Value','Round Off']] = combined_df[['Ass.Value', 'IGST Price (18%)', 'CGST Price (9%)', 'SGST Price (9%)', 'Invoice Value','Round Off']].applymap('{:.2f}'.format)
    combined_df.loc[combined_df['Sl No'] == 'Total', ['Round Off', 'HSN/SSC']] = ''
    column_order = ['Sl No', 'Customer Name', 'Customer GST Num', 'Invoice Number', 'Invoice Date', 'Quantity',
                        'Ass.Value', 'IGST Price (18%)', 'CGST Price (9%)', 'SGST Price (9%)', 'Invoice Value','Round Off','HSN/SSC']
    combined_df = combined_df[column_order]
    print("df")
    

   
    # Save the DataFrame to Excel file
    with pd.ExcelWriter('invoiceReports.xlsx', engine='xlsxwriter') as excel_writer:
      combined_df.to_excel(excel_writer, index=False)
 
    json_data = combined_df.to_json(orient='records')
    print(json_data,"json data")
            
    return json_data

    
    
  except Exception as e:
        print(e)
        return "invalid data"
    
    
from django.db.models import F

def po_report(request):
    try:
        print("entering po report")
        cust_id = request.GET.get('cust_id')
        print(cust_id, "cust id")
        po_no = request.GET.get('po_no')
        print("po no", po_no)
        queryset = Po.objects.all()

        if cust_id:
            queryset = queryset.filter(cust_id=cust_id)
        if po_no:
            queryset = queryset.filter(po_no=po_no)

        # Check if 'open_po' is a field in the model
        if 'open_po' in [field.name for field in Po._meta.get_fields()]:
            # If 'open_po' is True, select all columns without qty_sent__lt=F('qty')
            result = queryset.values(
                'cust_id', 'po_no', 'po_date', 'part_id', 'po_sl_no', 'open_po', 'open_po_validity', 'unit_price','qty', 'qty_sent'
            )
        else:
            # If 'open_po' is False, select only specific columns with qty_sent__lt=F('qty')
            result = queryset.filter(qty_sent__lt=F('qty')).values(
                'cust_id', 'po_no', 'po_date', 'part_id', 'po_sl_no', 'open_po', 'open_po_validity','unit_price', 'qty', 'qty_sent'
            )

        print(result, "values of result")

        df = pd.DataFrame(result)
        print(df, "df of po report")

        df = df.rename(columns={'cust_id': 'Customer ID', 'po_no': 'PO No', 'po_date': 'PO Date', 'part_id': 'Part Code',
                                'po_sl_no': 'PO Sl No', 'open_po': 'Open PO', 'open_po_validity': 'Open PO Validity', 'unit_price': 'Unit Price',
                                'qty': 'Total Quantity', 'qty_sent': 'Quantity Delivered'})

        if 'Open PO' in df.columns and not df[df['Open PO'] == 'Yes'].empty:
    # If 'Open PO' column is present and there are rows with 'Open PO' as 'Yes', set 'Quantity Balance' to 0
          df['Quantity Balance'] = 0
        else:
    # If 'Open PO' column is absent or there are no rows with 'Open PO' as 'Yes', calculate 'Quantity Balance'
          df['Quantity Balance'] = df['Total Quantity'] - df['Quantity Delivered']


        df['Open PO'] = df['Open PO'].apply(lambda x: 'Yes' if x else 'No')
        df['PO Date'] = pd.to_datetime(df['PO Date'], errors='coerce').dt.date
        df['PO Date']=pd.to_datetime(df['PO Date'], format='%Y-%m-%d').dt.strftime('%d-%m-%Y')
        df['PO Date'] = df['PO Date'].astype(str)
        df['Open PO Validity'] = df['Open PO Validity'].astype(str)
        df = df.sort_values(by=['Customer ID', 'PO No', 'PO Sl No'])
        df_json = df.to_json(orient='records')
        print(df_json, "........................................................")
        return JsonResponse({'data': df_json})
    except Exception as e:
        print(e)
        return JsonResponse({'error': 'invalid data'})

def inw_report(request):
 try:
    cust_id = request.GET.get('cust_id')
    po_no = request.GET.get('po_no')
    grn_no = request.GET.get('grn_no')
    queryset = InwDc.objects.filter(
            qty_delivered__lte=F('qty_received')
        )
    if cust_id:
            queryset = queryset.filter(cust_id=cust_id)
    if po_no:
            queryset = queryset.filter(po_no=po_no)
    if grn_no:
            queryset = queryset.filter(grn_no=grn_no)
    result = queryset.values(
            'cust_id', 'grn_no', 'grn_date', 'po_no', 'po_date',
            'po_sl_no', 'part_id', 'part_name', 'qty_received',
            'qty_delivered', 'qty_balance'
        )
    print(result, "values of result")
    df = pd.DataFrame(result)
    print(df, "df of po report")

   
    df = df.rename(columns={'cust_id': 'Customer ID','grn_no': 'Inward DC No', 'grn_date': 'Inward DC Date', 'po_no': 'PO No', 'po_date': 'PO Date', 'po_sl_no': 'PO Sl No', 'part_id': 'Part Code', 'part_name': 'Part Name', 'qty_received': 'Quantity Received', 'qty_delivered': 'Quantity Delivered', 'qty_balance': 'Quantity Balance'})
    df = df.sort_values(by=['Customer ID', 'Inward DC Date', 'Inward DC No', 'PO Sl No'])
    df['Inward DC Date'] = pd.to_datetime(df['Inward DC Date'], errors='coerce').dt.date
    df['Inward DC Date']=pd.to_datetime(df['Inward DC Date'], format='%Y-%m-%d').dt.strftime('%d-%m-%Y')
    df['Inward DC Date']= df['Inward DC Date'].astype(str) 
    df['PO Date'] = pd.to_datetime(df['PO Date'], errors='coerce').dt.date
    df['PO Date']=pd.to_datetime(df['PO Date'], format='%Y-%m-%d').dt.strftime('%d-%m-%Y')
    df['PO Date'] = df['PO Date'].astype(str)
    
    
    df_json = df.to_json(orient='records')
    print(df_json)

    return JsonResponse({'data': df_json})
      
 except Exception as e:
        print(e)
        return "invalid data"
    




    



