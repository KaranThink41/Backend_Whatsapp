# pharmacy/views.py
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Medicine, Category, Manufacturer, Pharmacy, 
    PharmacyInventory, Customer, Order, OrderItem,
    WhatsAppSession
)
from .serializers import (
    MedicineListSerializer, MedicineDetailSerializer, MedicineSearchSerializer,
    CategorySerializer, ManufacturerSerializer, PharmacySerializer,
    PharmacyInventorySerializer, CustomerSerializer, OrderSerializer,
    WhatsAppSessionSerializer, QuickOrderSerializer
)

# Medicine Views
class MedicineListView(generics.ListAPIView):
    queryset = Medicine.objects.filter(is_active=True)
    serializer_class = MedicineListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'manufacturer', 'form', 'prescription_type', 'is_in_stock']
    search_fields = ['name', 'generic_name', 'brand_name', 'composition']
    ordering_fields = ['name', 'mrp', 'created_at']
    ordering = ['name']

class MedicineDetailView(generics.RetrieveAPIView):
    queryset = Medicine.objects.filter(is_active=True)
    serializer_class = MedicineDetailSerializer

@api_view(['GET'])
def search_medicines(request):
    """Advanced medicine search for WhatsApp bot"""
    query = request.GET.get('q', '').strip()
    pharmacy_id = request.GET.get('pharmacy_id')
    limit = int(request.GET.get('limit', 10))
    
    if not query:
        return Response({'error': 'Search query is required'}, status=400)
    
    # Search in medicine names, generic names, and aliases
    medicines = Medicine.objects.filter(
        Q(name__icontains=query) |
        Q(generic_name__icontains=query) |
        Q(brand_name__icontains=query) |
        Q(aliases__alias__icontains=query),
        is_active=True
    ).distinct()[:limit]
    
    # If pharmacy_id provided, check stock availability
    if pharmacy_id:
        try:
            pharmacy = Pharmacy.objects.get(id=pharmacy_id)
            medicine_ids = medicines.values_list('id', flat=True)
            inventory = PharmacyInventory.objects.filter(
                pharmacy=pharmacy,
                medicine_id__in=medicine_ids,
                stock_quantity__gt=0
            ).values('medicine_id', 'stock_quantity')
            
            inventory_dict = {item['medicine_id']: item['stock_quantity'] for item in inventory}
            
            # Add stock info to serialized data
            serializer = MedicineSearchSerializer(medicines, many=True)
            data = serializer.data
            
            for item in data:
                item['stock_quantity'] = inventory_dict.get(item['id'], 0)
                item['available_at_pharmacy'] = item['stock_quantity'] > 0
            
            return Response(data)
        except Pharmacy.DoesNotExist:
            pass
    
    serializer = MedicineSearchSerializer(medicines, many=True)
    return Response(serializer.data)

# Category and Manufacturer Views
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ManufacturerListView(generics.ListAPIView):
    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer

# Pharmacy Views
class PharmacyListView(generics.ListAPIView):
    queryset = Pharmacy.objects.filter(is_active=True)
    serializer_class = PharmacySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'city', 'pincode']

class PharmacyDetailView(generics.RetrieveAPIView):
    queryset = Pharmacy.objects.filter(is_active=True)
    serializer_class = PharmacySerializer

@api_view(['GET'])
def pharmacy_inventory(request, pharmacy_id):
    """Get inventory for a specific pharmacy"""
    pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id, is_active=True)
    
    inventory = PharmacyInventory.objects.filter(
        pharmacy=pharmacy,
        stock_quantity__gt=0
    ).select_related('medicine')
    
    serializer = PharmacyInventorySerializer(inventory, many=True)
    return Response(serializer.data)

# Customer Views
class CustomerCreateView(generics.CreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

@api_view(['GET', 'POST'])
def customer_profile(request, phone_number):
    """Get or update customer profile"""
    try:
        customer = Customer.objects.get(phone_number=phone_number)
    except Customer.DoesNotExist:
        if request.method == 'POST':
            data = request.data.copy()
            data['phone_number'] = phone_number
            serializer = CustomerSerializer(data=data)
            if serializer.is_valid():
                customer = serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=400)
        else:
            return Response({'error': 'Customer not found'}, status=404)
    
    if request.method == 'GET':
        serializer = CustomerSerializer(customer)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CustomerSerializer(customer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

# Order Views
class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'customer', 'pharmacy']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        phone_number = self.request.GET.get('phone_number')
        if phone_number:
            return Order.objects.filter(customer__phone_number=phone_number)
        return Order.objects.all()

class OrderDetailView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    lookup_field = 'order_id'

@api_view(['POST'])
def create_quick_order(request):
    """Create order quickly through WhatsApp bot"""
    serializer = QuickOrderSerializer(data=request.data)
    if serializer.is_valid():
        order = serializer.save()
        order_serializer = OrderSerializer(order)
        return Response(order_serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['PATCH'])
def update_order_status(request, order_id):
    """Update order status"""
    try:
        order = Order.objects.get(order_id=order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)
    
    new_status = request.data.get('status')
    if new_status not in dict(Order.STATUS_CHOICES):
        return Response({'error': 'Invalid status'}, status=400)
    
    order.status = new_status
    order.save()
    
    serializer = OrderSerializer(order)
    return Response(serializer.data)

# WhatsApp Session Management
@api_view(['GET', 'POST'])
def whatsapp_session(request, phone_number):
    """Manage WhatsApp conversation sessions"""
    session_id = request.data.get('session_id', 'default') if request.method == 'POST' else request.GET.get('session_id', 'default')
    
    session, created = WhatsAppSession.objects.get_or_create(
        phone_number=phone_number,
        session_id=session_id,
        defaults={'current_step': 'start', 'context_data': {}}
    )
    
    if request.method == 'GET':
        serializer = WhatsAppSessionSerializer(session)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Update session data
        if 'current_step' in request.data:
            session.current_step = request.data['current_step']
        
        if 'context_data' in request.data:
            session.context_data.update(request.data['context_data'])
        
        session.save()
        serializer = WhatsAppSessionSerializer(session)
        return Response(serializer.data)

# Utility Views for WhatsApp Bot
@api_view(['GET'])
def medicine_suggestions(request):
    """Get medicine suggestions based on symptoms or conditions"""
    symptom = request.GET.get('symptom', '').strip().lower()
    limit = int(request.GET.get('limit', 5))
    
    if not symptom:
        return Response({'error': 'Symptom parameter is required'}, status=400)
    
    # Simple keyword matching (in production, use more sophisticated NLP)
    symptom_keywords = {
        'headache': ['paracetamol', 'aspirin', 'ibuprofen'],
        'fever': ['paracetamol', 'panadol', 'crocin'],
        'cold': ['cetirizine', 'phenylephrine', 'paracetamol'],
        'cough': ['dextromethorphan', 'ambroxol', 'salbutamol'],
        'acidity': ['omeprazole', 'pantoprazole', 'ranitidine'],
        'pain': ['ibuprofen', 'diclofenac', 'paracetamol'],
    }
    
    suggestions = []
    for condition, keywords in symptom_keywords.items():
        if condition in symptom:
            medicines = Medicine.objects.filter(
                Q(name__icontains=keywords[0]) |
                Q(generic_name__icontains=keywords[0]) |
                Q(composition__icontains=keywords[0]),
                is_active=True,
                prescription_type='OTC'  # Only suggest OTC medicines
            )[:limit]
            
            serializer = MedicineSearchSerializer(medicines, many=True)
            suggestions.extend(serializer.data)
            break
    
    return Response(suggestions[:limit])

@api_view(['GET'])
def pharmacy_nearby(request):
    """Find nearby pharmacies (simplified version)"""
    pincode = request.GET.get('pincode')
    city = request.GET.get('city')
    
    if not (pincode or city):
        return Response({'error': 'Pincode or city is required'}, status=400)
    
    pharmacies = Pharmacy.objects.filter(is_active=True)
    
    if pincode:
        pharmacies = pharmacies.filter(pincode=pincode)
    elif city:
        pharmacies = pharmacies.filter(city__icontains=city)
    
    serializer = PharmacySerializer(pharmacies, many=True)
    return Response(serializer.data)