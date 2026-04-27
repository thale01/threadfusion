from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Set if there is a discount")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Current selling price")
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    external_image_url = models.URLField(blank=True, null=True, help_text="Alternative to uploaded image (Google Drive/Image link)")
    stock = models.IntegerField(default=0)
    customization_label = models.CharField(max_length=100, blank=True, help_text="Label for customization field (e.g. 'Enter name')")
    enable_customization = models.BooleanField(default=False)
    available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def get_image_url(self):
        if self.external_image_url:
            return self.external_image_url
        if self.image:
            return self.image.url
        return "/static/images/placeholder.png" # Fallback if no image

    @property
    def discount_percentage(self):
        if self.original_price and self.original_price > self.price:
            discount = ((self.original_price - self.price) / self.original_price) * 100
            return int(discount)
        return 0

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    city = models.CharField(max_length=100)
    street_address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name}, {self.city}"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    is_gift = models.BooleanField(default=False)
    gift_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_subtotal(self):
        return sum(item.get_total_price() for item in self.items.all())
    
    def get_delivery_charge(self):
        return 0 # Free Shipping

    def get_discount_amount(self):
        if self.coupon and self.coupon.active:
            subtotal = self.get_subtotal()
            return (subtotal * self.coupon.discount) / 100
        return 0

    def get_total_price(self, gift_wrap=False):
        subtotal = self.get_subtotal()
        discount = self.get_discount_amount()
        total = subtotal - discount + self.get_delivery_charge()
        if gift_wrap:
            total += 50
        return total

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    customization_text = models.CharField(max_length=255, blank=True, null=True)
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    customization_image = models.ImageField(upload_to='customizations/', blank=True, null=True)

    def get_total_price(self):
        return self.product.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    gift_wrap = models.BooleanField(default=False)
    is_gift = models.BooleanField(default=False)
    gift_message = models.TextField(blank=True, null=True)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    custom_text = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    tracking_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"

class CustomImage(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    cart_item = models.ForeignKey('CartItem', on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    image = models.ImageField(upload_to='custom_uploads/')

    def __str__(self):
        return f"Image for {self.order or self.cart_item}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    customization_text = models.CharField(max_length=255, blank=True, null=True)
    customization_image = models.ImageField(upload_to='order_customizations/', blank=True, null=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class SocialPost(models.Model):
    title = models.CharField(max_length=200, blank=True)
    video_url = models.URLField(blank=True, null=True, help_text="Paste direct link to video/reel")
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Post {self.id}"

class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    review = models.TextField()
    rating = models.IntegerField(default=5)
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username}'s wishlist: {self.product.name}"

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount = models.IntegerField()  # percentage
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(auto_now_add=True)
    valid_to = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.code
