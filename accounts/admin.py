# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Wishlist

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profiles'
    fields = ('full_name', 'age', 'phone')

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'get_full_name', 'get_phone', 'date_joined', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'userprofile__full_name', 'userprofile__phone')
    
    def get_full_name(self, obj):
        return obj.userprofile.full_name if hasattr(obj, 'userprofile') and obj.userprofile.full_name else '-'
    get_full_name.short_description = 'Full Name'
    
    def get_phone(self, obj):
        return obj.userprofile.phone if hasattr(obj, 'userprofile') and obj.userprofile.phone else '-'
    get_phone.short_description = 'Phone'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'age', 'phone', 'city', 'country', 'get_email')
    list_filter = ('city', 'country')
    search_fields = ('user__username', 'full_name', 'phone', 'user__email')
    readonly_fields = ('user',)
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    search_fields = ('user__username', 'product__name')
    list_filter = ('added_at',)