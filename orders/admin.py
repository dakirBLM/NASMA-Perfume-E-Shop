# orders/admin.py
from django.contrib import admin
from .models import Order, OrderItem, Review

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'full_name', 'total_amount', 'status', 'created_at', 'has_tracking']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'full_name', 'email', 'id']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = [
        ('Order Information', {
            'fields': [
                'user', 'order_number', 'status',
                'total_amount', 'shipping_cost', 'tax_amount'
            ]
        }),
        ('Customer Information', {
            'fields': [
                'full_name', 'email', 'address', 'city', 
                'postal_code', 'country'
            ]
        }),
        ('Tracking Information', {
            'fields': [
                'tracking_company', 'tracking_number', 'tracking_url'
            ],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']

    def mark_as_processing(self, request, queryset):
        for order in queryset:
            old_status = order.status
            order.status = 'processing'
            order.save()
            # Email will be sent automatically via the save method
        self.message_user(request, f"Selected orders marked as Processing")
    mark_as_processing.short_description = "Mark selected orders as Processing"

    def mark_as_shipped(self, request, queryset):
        for order in queryset:
            old_status = order.status
            order.status = 'shipped'
            order.save()
        self.message_user(request, f"Selected orders marked as Shipped")
    mark_as_shipped.short_description = "Mark selected orders as Shipped"

    def mark_as_delivered(self, request, queryset):
        for order in queryset:
            old_status = order.status
            order.status = 'delivered'
            order.save()
        self.message_user(request, f"Selected orders marked as Delivered")
    mark_as_delivered.short_description = "Mark selected orders as Delivered"

    def mark_as_cancelled(self, request, queryset):
        for order in queryset:
            old_status = order.status
            order.status = 'cancelled'
            order.save()
        self.message_user(request, f"Selected orders marked as Cancelled")
    mark_as_cancelled.short_description = "Mark selected orders as Cancelled"
    
    def has_tracking(self, obj):
        return bool(obj.tracking_number)
    has_tracking.boolean = True
    has_tracking.short_description = 'Tracking'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'product__name', 'comment']
    readonly_fields = ['created_at', 'updated_at']