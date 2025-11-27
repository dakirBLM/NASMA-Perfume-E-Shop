# accounts/context_processors.py
from .models import Wishlist

def global_context(request):
    context = {}
    if request.user.is_authenticated:
        context['wishlist_count'] = Wishlist.objects.filter(user=request.user).count()
        # You can add cart_count here if you have a cart system
        # from orders.models import Cart
        # context['cart_count'] = Cart.objects.filter(user=request.user).count()
    else:
        context['wishlist_count'] = 0
        context['cart_count'] = 0  # Default value
    return context