from django.urls import path
from . import views
from .views import *
from .views import GetPOSlNoDetailsView

import sys

urlpatterns =[
    path('dc-printing/', DCPrint.as_view(), name='dc-printing'),
    path('invoice-printing/', InvoicePrint.as_view(), name='invoice-printing'),
    path('invoice-processing/', InvoiceProcessing.as_view(), name='invoice-processing'),
    path('inward-dc-input/', InwardDcInput.as_view(), name='inward-dc-input'),
    path('customer-master-input/', CustomerMasterInput.as_view(), name='customer-master-input'),
    path('purchase-order-input/', PurchaseOrderInput.as_view(), name='purchase-order-input'),
    path('part-master-input/', PartMasterInput.as_view(), name='part-master-input'),
    path("login/",LoginPage.as_view(),name='login'),
    path('logout/',LogoutPage.as_view(),name='logout'),
    path("signup/", SignUpPage.as_view(),name='signup'),
    path('invoice-report/', InvoiceReport.as_view(), name='invoice-report'),
    path('get-part-name/<str:part_id>/<str:cust_id>/', GetPartNameView.as_view(), name='get-part-name'),
    path('get-po-details/<path:po_no>/', GetPODetailsView.as_view(), name='get-po-details'),
    path('getAdditionalInfo/<path:po_no>/<int:po_sl_no>/', GetInfoView.as_view(), name='get-po-details'),
    path('i-p-details/<path:grn_no>/<int:po_sl_no>/', GetIPDetailsView.as_view(), name='i-p-details'),
    path('get-CN/<str:cust_id>/',GetCN.as_view(),name='get-CN'),
    path('get-inw-details/<path:grn_no>/', GetINWDetailsView.as_view(), name='get-inw-details'),
    path('get-po-sl-no-details/<path:po_no>/<path:part_id>/', GetPOSlNoDetailsView.as_view(), name='get-po-sl-no-details'),
    path('get-po-sl-no-details-inw/<path:grn_no>/<path:part_id>/', GetPOSlNoDetailsInwView.as_view(), name='get-po-sl-no-details-inw'),
]

