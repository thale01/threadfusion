from django.contrib import admin
from .models import Category, Product, Address, Cart, CartItem, Order, OrderItem, SocialPost, CustomImage, Review, Wishlist, Coupon
from django.utils.html import format_html

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'original_price', 'stock', 'enable_customization', 'available']
    list_filter = ['available', 'created', 'updated', 'category', 'enable_customization']
    list_editable = ['price', 'original_price', 'stock', 'available', 'enable_customization']
    search_fields = ['name', 'description']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ['product', 'price', 'quantity', 'customization_text', 'customization_image']
    readonly_fields = ['product', 'price', 'quantity', 'customization_text', 'customization_image']
    extra = 0

class CustomImageInline(admin.TabularInline):
    model = CustomImage
    extra = 0
    readonly_fields = ['preview', 'download_btn']

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" />', obj.image.url)
        return "-"

    def download_btn(self, obj):
        if obj.image:
            return format_html('<a href="{}" download class="button" style="background:#000; color:#fff; padding:5px 10px; border-radius:5px; text-decoration:none;">Download</a>', obj.image.url)
        return "-"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'full_name', 'total_price', 'status', 'is_gift', 'created_at']
    list_filter = ['status', 'is_gift', 'created_at']
    list_editable = ['status']
    search_fields = ['id', 'full_name', 'phone_number']
    inlines = [OrderItemInline, CustomImageInline]
    fieldsets = (
        ('Order Info', {
            'fields': ('user', 'full_name', 'phone_number', 'address', 'total_price', 'status', 'tracking_id')
        }),
        ('Gift Details', {
            'fields': ('is_gift', 'gift_message', 'gift_wrap')
        }),
    )

@admin.register(SocialPost)
class SocialPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at']
    list_filter = ['created_at']

from .models import Category, Product, Address, Cart, CartItem, Order, OrderItem, SocialPost, Testimonial

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['name', 'review']

admin.site.register(Address)
admin.site.register(Cart)
admin.site.register(CartItem)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount', 'active']
    list_filter = ['active']
