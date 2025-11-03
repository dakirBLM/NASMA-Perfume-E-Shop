from django.contrib import admin
from .models import Category, Collection, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    search_fields = ['name']
    list_filter = ['is_active', 'created_at']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_featured', 'is_new', 'stock_quantity']
    list_filter = ['category', 'collection', 'is_featured', 'is_new', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'image')
        }),
        ('Pricing', {
            'fields': ('price', 'original_price')
        }),
        ('Categorization', {
            'fields': ('category', 'collection')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'is_featured', 'is_new')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )