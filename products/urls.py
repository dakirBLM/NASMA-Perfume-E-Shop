# products/urls.py
from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('categories/', views.category_list, name='category_list'),
    path('collections/', views.collection_list, name='collection_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('collection/<int:collection_id>/', views.search_by_collection, name='search_by_collection'),
    path('category/<int:category_id>/', views.search_by_category, name='search_by_category'),
    path('product/<int:product_id>/review/', views.add_review, name='add_review'),  # Add this line
]