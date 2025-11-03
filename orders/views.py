# orders/views.py
import stripe
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.conf import settings

from products.models import Product
from .models import Order, OrderItem



def get_cart_data(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    cart_count = 0
    
    for product_id, item_data in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            quantity = item_data['quantity']
            item_total = product.price * quantity
            
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
            
            total += item_total
            cart_count += quantity
        except Product.DoesNotExist:
            continue
    
    return cart_items, total, cart_count

def cart_view(request):
    cart_items, total, cart_count = get_cart_data(request)
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'cart_count': cart_count
    }
    return render(request, 'orders/cart.html', context)

def add_to_cart(request, product_id):
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            data = json.loads(request.body)
            quantity = int(data.get('quantity', 1))
            
            if 'cart' not in request.session:
                request.session['cart'] = {}
            
            cart = request.session['cart']
            product_key = str(product_id)
            
            if product_key in cart:
                cart[product_key]['quantity'] += quantity
            else:
                cart[product_key] = {
                    'quantity': quantity,
                    'name': product.name,
                    'price': str(product.price)
                }
            
            request.session.modified = True
            cart_count = sum(item['quantity'] for item in cart.values())
            
            return JsonResponse({
                'success': True, 
                'message': f'{product.name} added to cart',
                'cart_count': cart_count
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def update_cart(request, product_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        cart = request.session.get('cart', {})
        if str(product_id) in cart:
            if quantity <= 0:
                del cart[str(product_id)]
            else:
                cart[str(product_id)]['quantity'] = quantity
            
            request.session.modified = True
            cart_count = sum(item['quantity'] for item in cart.values())
            
            return JsonResponse({'success': True, 'cart_count': cart_count})
        
        return JsonResponse({'success': False, 'message': 'Product not in cart'})

def remove_from_cart(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if str(product_id) in cart:
            del cart[str(product_id)]
            request.session.modified = True
            cart_count = sum(item['quantity'] for item in cart.values())
            return JsonResponse({'success': True, 'cart_count': cart_count})
        
        return JsonResponse({'success': False, 'message': 'Product not in cart'})

def clear_cart(request):
    if request.method == 'POST':
        request.session['cart'] = {}
        request.session.modified = True
        return JsonResponse({'success': True, 'cart_count': 0})

@login_required
def checkout_view(request):
    cart_items, total, cart_count = get_cart_data(request)
    
    if not cart_items:
        messages.error(request, 'Your cart is empty.')
        return redirect('orders:cart')
    
    # Updated for CZK - typical Czech shipping cost
    shipping_cost = 250  # 250 CZK instead of 10.00 EUR/USD
    tax_amount = 0  # Czech Republic has VAT, but we'll keep it simple for now
    final_total = total  + shipping_cost + tax_amount
    
    # Get user profile for pre-filling
    from accounts.models import UserProfile
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = None
    
    if request.method == 'POST':
        # Create order first (with pending status)
        order = Order.objects.create(
            user=request.user,
            full_name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            postal_code=request.POST.get('postal_code'),
            country=request.POST.get('country'),
           
            total_amount=total,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            status='pending'  # Will be confirmed after payment
        )
        
        # Create order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price
            )
        
        # Create Stripe Checkout Session with CZK
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'czk',  # Changed from 'usd' to 'czk'
                            'product_data': {
                                'name': f'Order #{order.order_number} - Golden Fragrance',
                            },
                            'unit_amount': int(final_total*100),  # CZK doesn't use cents, so no *100
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=request.build_absolute_uri(
                    f'/orders/payment-success/{order.id}/?session_id={{CHECKOUT_SESSION_ID}}'
                ),
                cancel_url=request.build_absolute_uri(
                    f'/orders/payment-cancel/{order.id}/'
                ),
                customer_email=request.user.email,
                metadata={
                    'order_id': order.id,
                    'user_id': request.user.id
                }
            )
            
            # Store Stripe session ID in order (you might want to add this field to your Order model)
            # If you don't have stripe_session_id field, add it to Order model or remove this line
            order.stripe_session_id = checkout_session.id
            order.save()
            
            # Redirect to Stripe Checkout
            return redirect(checkout_session.url)
            
        except Exception as e:
            messages.error(request, f'Payment error: {str(e)}')
            order.delete()  # Delete the order if payment fails
            return redirect('orders:checkout')
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'shipping_cost': shipping_cost,
        'tax_amount': tax_amount,
        'final_total': final_total,
        'cart_count': cart_count,
        'profile': profile,
        
    }
    return render(request, 'orders/checkout.html', context)

@login_required
def payment_success(request, order_id):
    session_id = request.GET.get('session_id')
    
    if not session_id:
        messages.error(request, 'Invalid payment session.')
        return redirect('orders:order_history')
    
    try:
        # Retrieve the Stripe session
        session = stripe.checkout.Session.retrieve(session_id)
        order = Order.objects.get(id=order_id, user=request.user)
        
        # Verify the payment was successful
        if session.payment_status == 'paid':
            # Update order status
            order.status = 'confirmed'
            order.stripe_payment_intent = session.payment_intent
            order.save()
            
            # Clear the cart
            request.session['cart'] = {}
            request.session.modified = True
            
            messages.success(request, f'Payment successful! Order #{order.order_number} has been confirmed.')
        else:
            messages.error(request, 'Payment was not successful. Please try again.')
            return redirect('orders:checkout')
            
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('orders:order_history')
    except Exception as e:
        messages.error(request, f'Error verifying payment: {str(e)}')
        return redirect('orders:order_history')
    
    return redirect('orders:order_detail', order_id=order.id)

@login_required
def payment_cancel(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        order.status = 'cancelled'
        order.save()
        messages.info(request, 'Payment was cancelled. You can try again anytime.')
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
    
    return redirect('orders:checkout')

# Add Stripe webhook handler for additional security
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Fulfill the purchase
        fulfill_order(session)

    return HttpResponse(status=200)

def fulfill_order(session):
    order_id = session.metadata.get('order_id')
    try:
        order = Order.objects.get(id=order_id)
        order.status = 'confirmed'
        order.stripe_payment_intent = session.payment_intent
        order.save()
    except Order.DoesNotExist:
        # Handle the error as appropriate for your application
        pass

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})