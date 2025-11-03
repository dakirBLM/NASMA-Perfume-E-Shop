from .models import Category, Collection

def categories_collections(request):
    cart_count = 0
    wishlist_count = 0
    
    if 'cart' in request.session:
        cart = request.session['cart']
        cart_count = sum(item['quantity'] for item in cart.values())
    
    if request.user.is_authenticated:
        from accounts.models import Wishlist
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
    
    return {
        'categories': Category.objects.all(),
        'collections': Collection.objects.filter(is_active=True),
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
    }