# products/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Category, Collection
# Remove this line: from .models import Review
from orders.models import Review  # Import Review from orders app

def home(request):
    featured_products = Product.objects.filter(is_featured=True)[:4]
    categories = Category.objects.all()[:3]
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'total_products': Product.objects.count(),
        'total_customers': 1000,
    }
    return render(request, 'home.html', context)

def product_list(request):
    products = Product.objects.all()
    
    # Filter by search query
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Filter by collection
    collection_id = request.GET.get('collection')
    if collection_id:
        products = products.filter(collection_id=collection_id)
    
    categories = Category.objects.all()
    collections = Collection.objects.filter(is_active=True)
    
    context = {
        'products': products,
        'categories': categories,
        'collections': collections,
        'search_query': query or '',
        'selected_category': category_id or '',
        'selected_collection': collection_id or '',
    }
    return render(request, 'products/product_list.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'products/product_detail.html', context)

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'products/category_list.html', {'categories': categories})

def collection_list(request):
    collections = Collection.objects.filter(is_active=True)
    return render(request, 'products/collection_list.html', {'collections': collections})

def search_by_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    products = Product.objects.filter(collection=collection)
    
    context = {
        'products': products,
        'collection': collection,
        'collections': Collection.objects.filter(is_active=True),
        'categories': Category.objects.all(),
        'selected_collection': str(collection_id),
    }
    return render(request, 'products/product_list.html', context)

def search_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    
    context = {
        'products': products,
        'category': category,
        'collections': Collection.objects.filter(is_active=True),
        'categories': Category.objects.all(),
        'selected_category': str(category_id),
    }
    return render(request, 'products/product_list.html', context)

@login_required
def add_review(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        # Check if user already reviewed this product
        existing_review = Review.objects.filter(user=request.user, product=product).first()
        
        if existing_review:
            existing_review.rating = rating
            existing_review.comment = comment
            existing_review.save()
            messages.success(request, 'Review updated successfully!')
        else:
            Review.objects.create(
                user=request.user,
                product=product,
                rating=rating,
                comment=comment
            )
            messages.success(request, 'Review added successfully!')
        
        return redirect('products:product_detail', product_id=product_id)
    
    return redirect('products:product_detail', product_id=product_id)