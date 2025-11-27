from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import Category, Collection, Product

@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']

@admin.register(Collection)
class CollectionAdmin(TranslationAdmin):
    list_display = ['name', 'is_active', 'created_at']
    search_fields = ['name']
    list_filter = ['is_active', 'created_at']

@admin.register(Product)
class ProductAdmin(TranslationAdmin):
    list_display = ['name', 'get_categories', 'price', 'is_featured', 'is_new', 'stock_quantity']
    list_filter = ['categories', 'collection', 'is_featured', 'is_new', 'created_at']
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
            'fields': ('categories', 'collection')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'is_featured', 'is_new')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_categories(self, obj):
        return ", ".join([c.name for c in obj.categories.all()])
    get_categories.short_description = 'Categories'