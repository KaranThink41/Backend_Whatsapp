# pharmacy/serializers.py
from rest_framework import serializers
from .models import (
    Medicine, Category, Manufacturer, Pharmacy, 
    PharmacyInventory, Customer, Order, OrderItem,
    WhatsAppSession, MedicineAlias
)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = '__all__'

class MedicineAliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicineAlias
        fields = ['alias']

class MedicineListSerializer(serializers.ModelSerializer):
    """Simplified serializer for medicine lists"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    manufacturer_name = serializers.CharField(source='manufacturer.name', read_only=True)
    selling_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'generic_name', 'brand_name', 'strength', 'form',
            'category_name', 'manufacturer_name', 'mrp', 'selling_price',
            'is_in_stock', 'prescription_type'
        ]

class MedicineDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual medicine"""
    category = CategorySerializer(read_only=True)
    manufacturer = ManufacturerSerializer(read_only=True)
    aliases = MedicineAliasSerializer(many=True, read_only=True)
    selling_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_prescription_required = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Medicine
        fields = '__all__'

class PharmacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pharmacy
        fields = '__all__'

class PharmacyInventorySerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    medicine_strength = serializers.CharField(source='medicine.strength', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    needs_reorder = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PharmacyInventory
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    medicine_strength = serializers.CharField(source='medicine.strength', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone_number', read_only=True)
    pharmacy_name = serializers.CharField(source='pharmacy.name', read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'

class WhatsAppSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppSession
        fields = '__all__'

# Specialized serializers for WhatsApp bot responses
class MedicineSearchSerializer(serializers.ModelSerializer):
    """Optimized for WhatsApp bot medicine search results"""
    category_name = serializers.CharField(source='category.name')
    manufacturer_name = serializers.CharField(source='manufacturer.name')
    selling_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'strength', 'form', 'selling_price', 
            'category_name', 'manufacturer_name', 'is_in_stock',
            'prescription_type'
        ]

class QuickOrderSerializer(serializers.Serializer):
    """For quick order creation through WhatsApp"""
    customer_phone = serializers.CharField(max_length=20)
    pharmacy_id = serializers.IntegerField()
    medicines = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField())
    )
    delivery_address = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def create(self, validated_data):
        # Custom order creation logic
        customer_phone = validated_data['customer_phone']
        pharmacy_id = validated_data['pharmacy_id']
        medicines_data = validated_data['medicines']
        
        # Get or create customer
        customer, created = Customer.objects.get_or_create(
            phone_number=customer_phone,
            defaults={'whatsapp_number': customer_phone}
        )
        
        # Create order
        order = Order.objects.create(
            customer=customer,
            pharmacy_id=pharmacy_id,
            delivery_address=validated_data.get('delivery_address', ''),
            notes=validated_data.get('notes', '')
        )
        
        total_amount = 0
        prescription_required = False
        
        # Create order items
        for med_data in medicines_data:
            try:
                medicine = Medicine.objects.get(id=med_data['medicine_id'])
                quantity = int(med_data['quantity'])
                
                unit_price = medicine.selling_price
                total_price = unit_price * quantity
                
                OrderItem.objects.create(
                    order=order,
                    medicine=medicine,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price
                )
                
                total_amount += total_price
                
                if medicine.is_prescription_required:
                    prescription_required = True
                    
            except Medicine.DoesNotExist:
                continue
        
        # Update order totals
        order.subtotal = total_amount
        order.tax_amount = total_amount * 0.05  # 5% tax
        order.total_amount = order.subtotal + order.tax_amount
        order.prescription_required = prescription_required
        order.save()
        
        return order