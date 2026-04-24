import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'threadfusion.settings')
django.setup()

from shop.models import Product, Category

# Ensure some products have discounts and customization enabled
p1 = Product.objects.first()
if p1:
    p1.original_price = p1.price + 200
    p1.enable_customization = True
    p1.customization_label = "Enter name for painting"
    p1.save()
    print(f"Updated {p1.name} with discount")

p2 = Product.objects.last()
if p2 and p2 != p1:
    p2.original_price = p2.price + 500
    p2.enable_customization = True
    p2.customization_label = "Message for the gift"
    p2.save()
    print(f"Updated {p2.name} with discount")
