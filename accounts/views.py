# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User 
from .models import Wishlist, UserProfile
from products.models import Product
from .forms import CustomUserCreationForm 

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Create the user AND profile through the form's save method
            user = form.save()
            
            # Log the user in
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    from django.contrib.auth import login as auth_login
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def profile_view(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        # Create a profile if it doesn't exist (for old users)
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        # Update user email
        user = request.user
        user.email = request.POST.get('email')
        user.save()
        
        # Update profile fields
        profile.full_name = request.POST.get('full_name')
        profile.phone = request.POST.get('phone')
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:profile')
    
    context = {
        'profile': profile,
    }
    return render(request, 'accounts/profile.html', context)

# ADD THE MISSING WISHLIST VIEW
@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    total_value = sum(item.product.price for item in wishlist_items)
    
    context = {
        'wishlist_items': wishlist_items,
        'total_value': total_value,
    }
    return render(request, 'accounts/wishlist.html', context)

@login_required
def add_to_wishlist(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        
        # Check if already in wishlist
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if created:
            message = f'{product.name} added to your wishlist!'
            success = True
        else:
            message = f'{product.name} is already in your wishlist!'
            success = False
        
        # Get updated wishlist count
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
        
        return JsonResponse({
            'success': success, 
            'message': message,
            'action': 'added' if created else 'exists',
            'wishlist_count': wishlist_count
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def remove_from_wishlist(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        
        try:
            wishlist_item = Wishlist.objects.get(user=request.user, product=product)
            wishlist_item.delete()
            
            # Get updated wishlist count
            wishlist_count = Wishlist.objects.filter(user=request.user).count()
            
            return JsonResponse({
                'success': True, 
                'message': f'{product.name} removed from your wishlist!',
                'action': 'removed',
                'wishlist_count': wishlist_count
            })
        except Wishlist.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'message': 'Product not found in your wishlist!'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def toggle_wishlist(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        
        try:
            wishlist_item = Wishlist.objects.get(user=request.user, product=product)
            wishlist_item.delete()
            action = 'removed'
            message = f'{product.name} removed from your wishlist!'
        except Wishlist.DoesNotExist:
            Wishlist.objects.create(user=request.user, product=product)
            action = 'added'
            message = f'{product.name} added to your wishlist!'
        
        # Get updated wishlist count
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
        
        return JsonResponse({
            'success': True, 
            'message': message,
            'action': action,
            'wishlist_count': wishlist_count
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})