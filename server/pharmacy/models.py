# pharmacy/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

class Category(models.Model):
    """Medicine categories like Antibiotics, Painkillers, etc."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name

class Manufacturer(models.Model):
    """Pharmaceutical companies"""
    name = models.CharField(max_length=200, unique=True)
    country = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Medicine(models.Model):
    """Main medicine model"""
    PRESCRIPTION_CHOICES = [
        ('OTC', 'Over the Counter'),
        ('RX', 'Prescription Required'),
        ('RXC', 'Prescription Required - Controlled'),
    ]
    
    FORM_CHOICES = [
        ('TAB', 'Tablet'),
        ('CAP', 'Capsule'),
        ('SYR', 'Syrup'),
        ('INJ', 'Injection'),
        ('CRE', 'Cream'),
        ('OIN', 'Ointment'),
        ('DRP', 'Drops'),
        ('SPR', 'Spray'),
        ('INH', 'Inhaler'),
        ('SUP', 'Suppository'),
    ]
    
    # Basic Info
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    brand_name = models.CharField(max_length=200, blank=True)
    
    # Classification
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE)
    
    # Medicine Details
    composition = models.TextField(help_text="Active ingredients")
    strength = models.CharField(max_length=100, help_text="e.g., 500mg, 10mg/ml")
    form = models.CharField(max_length=3, choices=FORM_CHOICES)
    pack_size = models.CharField(max_length=50, help_text="e.g., 10 tablets, 100ml")
    
    # Prescription Info
    prescription_type = models.CharField(max_length=3, choices=PRESCRIPTION_CHOICES, default='OTC')
    
    # Usage Info
    indication = models.TextField(help_text="What it's used for")
    dosage = models.TextField(help_text="How to use")
    side_effects = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)
    
    # Pricing
    mrp = models.DecimalField(max_digits=10, decimal_places=2, help_text="Maximum Retail Price")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, 
                                            validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Stock & Status
    is_active = models.BooleanField(default=True)
    is_in_stock = models.BooleanField(default=True)
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['name', 'strength', 'manufacturer']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['generic_name']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.strength}"
    
    @property
    def selling_price(self):
        """Calculate selling price after discount"""
        discount_amount = (self.mrp * self.discount_percentage) / 100
        return self.mrp - discount_amount
    
    @property
    def is_prescription_required(self):
        return self.prescription_type in ['RX', 'RXC']

class MedicineAlias(models.Model):
    """Alternative names for medicines to improve search"""
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='aliases')
    alias = models.CharField(max_length=200)
    
    class Meta:
        unique_together = ['medicine', 'alias']
    
    def __str__(self):
        return f"{self.alias} -> {self.medicine.name}"

class Pharmacy(models.Model):
    """Pharmacy/Medical store information"""
    name = models.CharField(max_length=200)
    license_number = models.CharField(max_length=100, unique=True)
    owner_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    
    # Business Hours
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_24x7 = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Pharmacies"
    
    def __str__(self):
        return self.name

class PharmacyInventory(models.Model):
    """Track medicine stock at each pharmacy"""
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    
    stock_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    batch_number = models.CharField(max_length=50, blank=True)
    expiry_date = models.DateField()
    
    # Pricing (can be different from MRP)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['pharmacy', 'medicine', 'batch_number']
    
    def __str__(self):
        return f"{self.pharmacy.name} - {self.medicine.name} ({self.stock_quantity})"
    
    @property
    def is_expired(self):
        return self.expiry_date < timezone.now().date()
    
    @property
    def needs_reorder(self):
        return self.stock_quantity <= self.reorder_level

class Customer(models.Model):
    """Customer information for order tracking"""
    phone_number = models.CharField(max_length=20, unique=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    
    # Preferences
    preferred_pharmacy = models.ForeignKey(Pharmacy, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name or 'Customer'} - {self.phone_number}"

class Order(models.Model):
    """Orders placed through WhatsApp bot"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('PREPARING', 'Preparing'),
        ('READY', 'Ready for Pickup'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    
    # Totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Additional Info
    prescription_required = models.BooleanField(default=False)
    prescription_uploaded = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    # Delivery
    delivery_address = models.TextField(blank=True)
    delivery_time = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.order_id} - {self.customer.name}"

class OrderItem(models.Model):
    """Individual items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"

class WhatsAppSession(models.Model):
    """Track WhatsApp conversation sessions"""
    phone_number = models.CharField(max_length=20)
    session_id = models.CharField(max_length=100)
    
    # Current state
    current_step = models.CharField(max_length=50, default='start')
    context_data = models.JSONField(default=dict)  # Store conversation context
    
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['phone_number', 'session_id']
    
    def __str__(self):
        return f"{self.phone_number} - {self.current_step}"