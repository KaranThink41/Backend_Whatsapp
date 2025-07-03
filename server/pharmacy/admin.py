# pharmacy/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Manufacturer, Medicine, MedicineAlias, 
    Pharmacy, PharmacyInventory, Customer, Order, OrderItem,
    WhatsAppSession
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']
    list_per_page = 20

@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'contact_email', 'phone', 'created_at']
    search_fields = ['name', 'country']
    list_filter = ['country', 'created_at']
    list_per_page = 20

class MedicineAliasInline(admin.TabularInline):
    model = MedicineAlias
    extra = 1

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'generic_name', 'strength', 'form', 'category', 
        'manufacturer', 'mrp', 'selling_price_display', 'discount_percentage', 'prescription_type', 
        'is_in_stock', 'is_active'
    ]
    list_filter = [
        'category', 'manufacturer', 'form', 'prescription_type', 
        'is_active', 'is_in_stock', 'created_at'
    ]
    search_fields = ['name', 'generic_name', 'brand_name', 'composition']
    readonly_fields = ['created_at', 'updated_at', 'selling_price_display']
    list_editable = ['is_active', 'is_in_stock', 'mrp', 'discount_percentage']
    list_per_page = 25
    inlines = [MedicineAliasInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'generic_name', 'brand_name', 'category', 'manufacturer')
        }),
        ('Medicine Details', {
            'fields': ('composition', 'strength', 'form', 'pack_size', 'prescription_type')
        }),
        ('Usage Information', {
            'fields': ('indication', 'dosage', 'side_effects', 'contraindications'),
            'classes': ('collapse',)
        }),
        ('Pricing', {
            'fields': ('mrp', 'discount_percentage', 'selling_price_display')
        }),
        ('Status', {
            'fields': ('is_active', 'is_in_stock')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def selling_price_display(self, obj):
        return f"₹{obj.selling_price:.2f}"
    selling_price_display.short_description = "Selling Price"

@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'license_number', 'owner_name', 'phone', 
        'city', 'state', 'pincode', 'is_24x7', 'is_active'
    ]
    list_filter = ['city', 'state', 'is_24x7', 'is_active', 'created_at']
    search_fields = ['name', 'license_number', 'owner_name', 'phone', 'city', 'pincode']
    list_editable = ['is_active']
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'license_number', 'owner_name')
        }),
        ('Contact Information', {
            'fields': ('phone', 'whatsapp_number', 'email')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'pincode')
        }),
        ('Business Hours', {
            'fields': ('opening_time', 'closing_time', 'is_24x7')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )

@admin.register(PharmacyInventory)
class PharmacyInventoryAdmin(admin.ModelAdmin):
    list_display = [
        'pharmacy', 'medicine', 'stock_quantity', 'reorder_level',
        'batch_number', 'expiry_date', 'is_expired', 'needs_reorder'
    ]
    list_filter = [
        'pharmacy', 'medicine__category', 'expiry_date', 'created_at'
    ]
    search_fields = [
        'pharmacy__name', 'medicine__name', 'batch_number'
    ]
    list_editable = ['stock_quantity', 'reorder_level']
    readonly_fields = ['is_expired', 'needs_reorder', 'created_at', 'updated_at']
    list_per_page = 30
    
    def is_expired(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">Yes</span>')
        return format_html('<span style="color: green;">No</span>')
    is_expired.short_description = "Expired"
    
    def needs_reorder(self, obj):
        if obj.needs_reorder:
            return format_html('<span style="color: orange;">Yes</span>')
        return format_html('<span style="color: green;">No</span>')
    needs_reorder.short_description = "Needs Reorder"

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'phone_number', 'whatsapp_number', 'email',
        'city', 'pincode', 'preferred_pharmacy', 'created_at'
    ]
    list_filter = ['city', 'preferred_pharmacy', 'created_at']
    search_fields = ['name', 'phone_number', 'email']
    list_per_page = 25

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['total_price']
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_id_short', 'customer', 'pharmacy', 'status',
        'total_amount', 'prescription_required', 'created_at'
    ]
    list_filter = [
        'status', 'pharmacy', 'prescription_required', 
        'prescription_uploaded', 'created_at'
    ]
    search_fields = ['order_id', 'customer__name', 'customer__phone_number']
    readonly_fields = [
        'order_id', 'subtotal', 'tax_amount', 'total_amount',
        'created_at', 'updated_at'
    ]
    list_editable = ['status']
    list_per_page = 20
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'customer', 'pharmacy', 'status')
        }),
        ('Order Details', {
            'fields': ('prescription_required', 'prescription_uploaded', 'notes')
        }),
        ('Delivery Information', {
            'fields': ('delivery_address', 'delivery_time')
        }),
        ('Payment Summary', {
            'fields': ('subtotal', 'tax_amount', 'delivery_charge', 'total_amount'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def order_id_short(self, obj):
        return str(obj.order_id)[:8] + "..."
    order_id_short.short_description = "Order ID"

@admin.register(WhatsAppSession)
class WhatsAppSessionAdmin(admin.ModelAdmin):
    list_display = [
        'phone_number', 'session_id', 'current_step',
        'last_activity', 'created_at'
    ]
    list_filter = ['current_step', 'last_activity', 'created_at']
    search_fields = ['phone_number', 'session_id']
    readonly_fields = ['created_at', 'last_activity']
    list_per_page = 30
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['phone_number', 'session_id']
        return self.readonly_fields

# Customize admin site
admin.site.site_header = "Pharmacy Management System"
admin.site.site_title = "Pharmacy Admin"
admin.site.index_title = "Welcome to Pharmacy Management System"