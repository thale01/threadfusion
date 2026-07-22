import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'threadfusion.settings')
django.setup()

from shop.models import Category, Product
from django.contrib.auth.models import User
from django.core.files import File

def setup():
    # 1. Create Superuser if doesn't exist
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("Superuser created: admin / admin123")

    # 2. Create Categories
    pottery, _ = Category.objects.get_or_create(name='Pottery', slug='pottery')
    textiles, _ = Category.objects.get_or_create(name='Textiles', slug='textiles')
    accessories, _ = Category.objects.get_or_create(name='Accessories', slug='accessories')
    print("Categories created")

    # 3. Create initial product if it doesn't exist
    if not Product.objects.exists():
        p1 = Product(
            category=pottery,
            name='Ocean Mist Vase',
            description='A beautiful hand-thrown ceramic vase with a unique turquoise mist glaze. Perfect for dried flowers or as a standalone art piece.',
            price=45.00,
            customization_label='Engraving (Optional)'
        )
        # Use the generated image if it exists
        img_path = 'media/products/pottery.png'
        if os.path.exists(img_path):
            with open(img_path, 'rb') as f:
                p1.image.save('pottery.png', File(f), save=False)
        p1.save()
        print("Initial product created: Ocean Mist Vase")

if __name__ == '__main__':
    setup()
