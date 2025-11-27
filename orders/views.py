# orders/views.py
import stripe
import json
from decimal import Decimal
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.conf import settings

from products.models import Product
from .models import Order, OrderItem, Coupon

stripe.api_key = settings.STRIPE_SECRET_KEY

# Currency helpers for CZK (Stripe expects minor unit, haléř)
def czk_to_minor(amount_whole_czk):
    """Convert stored whole CZK integer/Decimal to minor units for Stripe."""
    if amount_whole_czk is None:
        return 0
    return int(Decimal(amount_whole_czk) * 100)

def minor_to_czk(amount_minor):
    if amount_minor is None:
        return 0
    return int(Decimal(amount_minor) / 100)

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
    
    # CZK handling: all stored as whole koruna integers (no decimals in DB)
    shipping_cost = 250  # Flat shipping in CZK
    tax_amount = 0  # Simplified (extend with proper VAT later)
    discount_amount = 0
    applied_coupon = None

    # If user submitted a coupon on GET via query or prior session, we could preload it (optional)
    if request.method == 'POST':
        code = (request.POST.get('coupon_code') or '').strip()
        if code:
            try:
                coupon = Coupon.objects.get(code__iexact=code, is_active=True)
                # Validate date window if provided
                from django.utils import timezone
                now = timezone.now()
                if (coupon.valid_from and coupon.valid_from > now) or (coupon.valid_to and coupon.valid_to < now):
                    messages.error(request, 'This coupon is not currently valid.')
                else:
                    discount_amount = int(coupon.amount)
                    applied_coupon = coupon
            except Coupon.DoesNotExist:
                messages.error(request, 'Invalid coupon code.')

    # Compute final total with discount (never below zero)
    final_total = max(0, (total + shipping_cost + tax_amount) - discount_amount)
    
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
            discount_amount=discount_amount,
            coupon_code=(applied_coupon.code if applied_coupon else None),
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
        
        # Build line items for Stripe Checkout
        line_items = []
        if discount_amount and final_total >= 0:
            # Simpler: charge a single consolidated line equal to final total
            line_items.append({
                'price_data': {
                    'currency': 'czk',
                    'product_data': {
                        'name': 'Order Total (incl. discount)',
                    },
                    'unit_amount': czk_to_minor(final_total),
                },
                'quantity': 1,
            })
        else:
            for item in cart_items:
                line_items.append({
                    'price_data': {
                        'currency': 'czk',
                        'product_data': {
                            'name': item['product'].name,
                        },
                        'unit_amount': czk_to_minor(item['product'].price),
                    },
                    'quantity': item['quantity'],
                })
            if shipping_cost > 0:
                line_items.append({
                    'price_data': {
                        'currency': 'czk',
                        'product_data': {
                            'name': 'Shipping',
                        },
                        'unit_amount': czk_to_minor(shipping_cost),
                    },
                    'quantity': 1,
                })
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                client_reference_id=str(order.id),
                success_url=request.build_absolute_uri(
                    f'/orders/payment-success/{order.id}/?session_id={{CHECKOUT_SESSION_ID}}'
                ),
                cancel_url=request.build_absolute_uri(
                    f'/orders/payment-cancel/{order.id}/'
                ),
                customer_email=request.user.email,
                metadata={
                    'order_id': order.id,
                    'user_id': request.user.id,
                    'order_number': order.order_number,
                    'coupon_code': order.coupon_code or '',
                },
                idempotency_key=f'order_checkout_{order.id}'
            )
            order.stripe_session_id = checkout_session.id
            order.save()
            return redirect(checkout_session.url)
        except Exception as e:
            messages.error(request, f'Payment error: {str(e)}')
            order.delete()
            return redirect('orders:checkout')
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'shipping_cost': shipping_cost,
        'tax_amount': tax_amount,
        'final_total': final_total,
        'discount_amount': discount_amount,
        'applied_coupon': applied_coupon.code if applied_coupon else '',
        'cart_count': cart_count,
        'profile': profile,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY
    }
    return render(request, 'orders/checkout.html', context)

@login_required
def payment_success(request, order_id):
    session_id = request.GET.get('session_id')
    
    if not session_id:
        messages.error(request, 'Invalid payment session.')
        return redirect('orders:order_history')
    
    try:
        # Retrieve the Stripe session & expand payment_intent
        session = stripe.checkout.Session.retrieve(session_id, expand=['payment_intent'])
        order = Order.objects.get(id=order_id, user=request.user)
        if str(order.id) != session.metadata.get('order_id'):
            messages.error(request, 'Session/order mismatch.')
            return redirect('orders:order_history')
        if session.payment_status == 'paid':
            payment_intent = session.payment_intent
            if isinstance(payment_intent, dict):  # expanded
                amount_received_minor = payment_intent.get('amount_received')
                payment_intent_id = payment_intent.get('id')
            else:
                pi = stripe.PaymentIntent.retrieve(session.payment_intent)
                amount_received_minor = pi.amount_received
                payment_intent_id = pi.id
            order.mark_as_paid(payment_intent_id, amount_received_minor)
            request.session['cart'] = {}
            request.session.modified = True
            messages.success(request, f'Payment successful! Order #{order.order_number} confirmed.')
        else:
            messages.error(request, 'Payment not completed.')
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
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    if sig_header is None:
        return HttpResponse(status=400)
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    event_type = event.get('type')
    data_object = event['data']['object']

    if event_type == 'checkout.session.completed':
        session = data_object
        order_id = session.get('metadata', {}).get('order_id')
        payment_intent_id = session.get('payment_intent')
        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(id=order_id)
                if order.status != 'confirmed':
                    # Retrieve payment intent for amount
                    pi = stripe.PaymentIntent.retrieve(payment_intent_id)
                    amount_received_minor = pi.amount_received
                    order.mark_as_paid(payment_intent_id, amount_received_minor)
        except Order.DoesNotExist:
            pass
    elif event_type == 'payment_intent.succeeded':
        payment_intent_id = data_object.get('id')
        metadata = data_object.get('metadata', {})
        order_id = metadata.get('order_id')
        if order_id:
            try:
                with transaction.atomic():
                    order = Order.objects.select_for_update().get(id=order_id)
                    if order.status != 'confirmed':
                        amount_received_minor = data_object.get('amount_received')
                        order.mark_as_paid(payment_intent_id, amount_received_minor)
            except Order.DoesNotExist:
                pass
    # Extend with other event types as needed
    return HttpResponse(status=200)

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})