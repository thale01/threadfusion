from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Address, SocialPost, Review, Wishlist, Coupon, CustomImage, Testimonial, BusinessSettings
from django.db.models import Q, Avg, Sum, Count
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
import io
import zipfile
import os

def home(request):
    featured_products = Product.objects.filter(available=True).order_by('-is_featured', '-created')[:8]
    categories = Category.objects.all()
    posts = SocialPost.objects.all().order_by('-created_at')[:8]
    testimonials = Testimonial.objects.all().order_by('-created_at')[:6]
    return render(request, 'shop/home.html', {
        'featured_products': featured_products,
        'categories': categories,
        'posts': posts,
        'testimonials': testimonials
    })

def returns_view(request):
    return render(request, 'shop/returns.html')

def contact_view(request):
    if request.method == 'POST':
        # In a real app, you would send an email or save the message
        messages.success(request, "Thank you! Your message has been sent. We'll get back to you soon.")
        return redirect('contact')
    return render(request, 'shop/contact.html')

def shipping_view(request):
    return render(request, 'shop/shipping.html')

def product_list(request):
    category_slug = request.GET.get('category')
    search_query = request.GET.get('search')
    sort_by = request.GET.get('sort')
    filter_by = request.GET.get('filter')
    
    products = Product.objects.filter(available=True)
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )

    if filter_by == 'featured':
        products = products.filter(is_featured=True)
    
    if sort_by == 'newest':
        products = products.order_by('-created_at')
        
    categories = Category.objects.all()
    return render(request, 'shop/product_list.html', {
        'products': products,
        'categories': categories,
        'search_query': search_query
    })

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    reviews = product.reviews.all().order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    
    # Check if user has purchased this product to show "Verified Purchase"
    verified_purchase = False
    if request.user.is_authenticated:
        verified_purchase = OrderItem.objects.filter(order__user=request.user, product=product, order__status='Delivered').exists()

    settings_obj = BusinessSettings.objects.first()

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'in_wishlist': in_wishlist,
        'verified_purchase': verified_purchase,
        'settings': settings_obj
    })

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def profile_view(request):
    addresses = Address.objects.filter(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/profile.html', {
        'addresses': addresses,
        'orders': orders
    })

@login_required
def add_address(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        city = request.POST.get('city')
        street = request.POST.get('street')
        zip_code = request.POST.get('zip')
        
        Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone_number=phone,
            city=city,
            street_address=street,
            postal_code=zip_code
        )
        messages.success(request, "Address added successfully!")
        return redirect('profile')
    return render(request, 'shop/add_address.html')

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    return None

@login_required
def cart_view(request):
    cart = get_or_create_cart(request)
    return render(request, 'shop/cart.html', {'cart': cart})

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity_raw = request.POST.get('quantity', 1)
        customization = request.POST.get('custom_text')
        customer_name = request.POST.get('customer_name')
        images = request.FILES.getlist('custom_images')
        
        product = get_object_or_404(Product, id=product_id)
        cart = get_or_create_cart(request)
        
        try:
            quantity = int(quantity_raw)
        except (ValueError, TypeError):
            quantity = 1
            
        size_id = request.POST.get('size_id')
        size_str = None
        price_override = None
        base_price = product.price

        if product.enable_size_selection:
            if size_id:
                from .models import ProductSize
                try:
                    ps = ProductSize.objects.get(id=size_id, product=product)
                    size_str = ps.size
                    base_price = ps.price
                    price_override = base_price
                except ProductSize.DoesNotExist:
                    pass

        custom_name = None
        letter_count = None
        extra_letter_charges = None

        if product.enable_name_pricing:
            custom_name = request.POST.get('custom_name', '').strip()
            # Clean and get length of the name
            cleaned_name = custom_name.replace(" ", "")
            letter_count = len(cleaned_name)
            if letter_count > product.included_letters:
                extra_letter_charges = (letter_count - product.included_letters) * product.extra_letter_price
            else:
                extra_letter_charges = 0
            price_override = int(base_price) + int(extra_letter_charges)
        elif product.enable_size_selection and size_str:
            # Set price override to selected size price even if name pricing is disabled
            price_override = int(base_price)
            
        frame_color = request.POST.get('frame_color')
        thread_color = request.POST.get('thread_color')
        led_option = request.POST.get('led_option') == 'on'

        cart_item = CartItem.objects.create(
            cart=cart, 
            product=product,
            product_size=size_str,
            price_override=price_override,
            quantity=quantity,
            customization_text=customization,
            customer_name=customer_name,
            custom_name=custom_name,
            letter_count=letter_count,
            extra_letter_charges=extra_letter_charges,
            frame_color=frame_color,
            thread_color=thread_color,
            led_option=led_option
        )
        
        # Save multiple images to CustomImage linked to CartItem
        for img in images:
            CustomImage.objects.create(cart_item=cart_item, image=img)
        
        # Gift option
        is_gift = request.POST.get('is_gift') == 'on'
        gift_message = request.POST.get('gift_message', '')
        
        if is_gift:
            cart.is_gift = True
            cart.gift_message = gift_message
            cart.save()

        messages.success(request, f"✔ {product.name} added to cart.")
        return redirect('cart')
    
    return redirect('product_list')

@login_required
def update_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    action = request.POST.get('action')
    if action == 'increase':
        item.quantity += 1
    elif action == 'decrease' and item.quantity > 1:
        item.quantity -= 1
    item.save()
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect('cart')

@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    if not cart or not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('product_list')
    
    addresses = Address.objects.filter(user=request.user)
    
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        gift_wrap = request.POST.get('gift_wrap') == 'on'
        customer_name = request.POST.get('customer_name', request.user.get_full_name() or request.user.username)
        address = get_object_or_404(Address, id=address_id, user=request.user)
        
        order = Order.objects.create(
            user=request.user,
            full_name=address.full_name,
            phone_number=address.phone_number,
            address=f"{address.street_address}, {address.city}, {address.postal_code}",
            total_price=cart.get_total_price(gift_wrap=gift_wrap),
            gift_wrap=gift_wrap,
            is_gift=cart.is_gift,
            gift_message=cart.gift_message,
            delivery_charge=cart.get_delivery_charge(),
            custom_text=request.POST.get('custom_text', '')  # Save general custom text
        )
        
        clean_name = customer_name.replace(" ", "_")
        image_count = 1

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_size=item.product_size,
                price=item.price_override if item.price_override is not None else item.product.price,
                quantity=item.quantity,
                customization_text=item.customization_text,
                customization_image=item.customization_image,
                custom_name=item.custom_name,
                letter_count=item.letter_count,
                extra_letter_charges=item.extra_letter_charges,
                frame_color=item.frame_color,
                thread_color=item.thread_color,
                led_option=item.led_option
            )
            
            # Move and rename CustomImages from CartItem to Order
            item_name = item.customer_name or clean_name
            item_clean_name = item_name.replace(" ", "_")
            
            for c_img in item.images.all():
                ext = os.path.splitext(c_img.image.name)[1]
                new_filename = f"{item_clean_name}_order{order.id}_{image_count}{ext}"
                c_img.image.name = new_filename
                c_img.order = order
                c_img.cart_item = None
                c_img.save()
                image_count += 1

        cart.items.all().delete()
        messages.success(request, "✔ Order placed successfully!")
        messages.info(request, "📸 Please send payment screenshot via WhatsApp for confirmation.")
        return redirect('order_history')
        
    return render(request, 'shop/checkout.html', {
        'cart': cart,
        'addresses': addresses
    })

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/order_history.html', {'orders': orders})

@login_required
def order_detail(request, id):
    order = get_object_or_404(Order, id=id, user=request.user)
    return render(request, 'shop/order_detail.html', {'order': order})

def customize_view(request):
    return render(request, 'shop/customize.html')

@login_required
def generate_invoice(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
        elements = []

        styles = getSampleStyleSheet()
        
        # Colors
        navy = colors.HexColor('#0C2C47')
        blush = colors.HexColor('#EFEAE6')
        mauve = colors.HexColor('#b08968')
        text_color = colors.HexColor('#333333')

        # Custom Styles
        title_style = ParagraphStyle(
            'TitleStyle', parent=styles['Heading1'], fontSize=28, textColor=navy, 
            fontName='Helvetica-Bold', alignment=0, spaceAfter=2
        )
        tagline_style = ParagraphStyle(
            'TaglineStyle', fontSize=10, textColor=mauve, 
            fontName='Helvetica-Oblique', alignment=0, spaceAfter=20
        )
        section_title = ParagraphStyle(
            'SectionTitle', fontSize=12, textColor=navy, 
            fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=5
        )
        normal_style = ParagraphStyle(
            'NormalStyle', fontSize=10, textColor=text_color, fontName='Helvetica', leading=14
        )
        status_style = ParagraphStyle(
            'StatusStyle', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold',
            alignment=1, borderPadding=3, borderRadius=5, backColor=navy
        )

        # Header Table: Brand (Left) | Invoice Info (Right)
        brand_info = [
            [
                Paragraph(f"THREADFUSION", title_style),
                Paragraph(f"INVOICE #TF-{order.id}", ParagraphStyle('RightBold', parent=normal_style, fontSize=16, fontName='Helvetica-Bold', alignment=2))
            ],
            [
                Paragraph("Handmade with love", tagline_style),
                Paragraph(f"Date: {order.created_at.strftime('%d %b, %Y')}", ParagraphStyle('RightSmall', parent=normal_style, alignment=2))
            ]
        ]
        header_table = Table(brand_info, colWidths=[100*mm, 70*mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 15*mm))

        # Billing Info Table
        billing_data = [
            [Paragraph("Billed To:", section_title), Paragraph("Order Details:", section_title)],
            [
                Paragraph(f"<b>{order.full_name}</b><br/>{order.address}<br/>Phone: {order.phone_number}", normal_style),
                Paragraph(f"Status: <b>{order.status}</b><br/>Payment: Cash on Delivery", normal_style)
            ]
        ]
        billing_table = Table(billing_data, colWidths=[85*mm, 85*mm])
        billing_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        elements.append(billing_table)
        elements.append(Spacer(1, 10*mm))

        # Product Table
        table_data = [['Product Details', 'Price', 'Qty', 'Total']]
        for item in order.items.all():
            product_desc = f"<b>{item.product.name}</b>"
            if item.product_size:
                product_desc += f" ({item.product_size})"
            if item.custom_name:
                product_desc += f"<br/><font size='8' color='{mauve}'>Name: {item.custom_name}</font>"
            if item.customization_text:
                product_desc += f"<br/><font size='8' color='{mauve}'>Note: {item.customization_text}</font>"
            
            table_data.append([
                Paragraph(product_desc, normal_style),
                f"₹{item.price}",
                str(item.quantity),
                f"₹{item.price * item.quantity}"
            ])

        prod_table = Table(table_data, colWidths=[90*mm, 25*mm, 20*mm, 35*mm])
        prod_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), blush),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, blush]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 1), (-1, -1), 10),
            ('RIGHTPADDING', (-1, 1), (-1, -1), 10),
        ]))
        elements.append(prod_table)
        elements.append(Spacer(1, 10*mm))

        # Financial Summary
        delivery_fee = order.delivery_charge
        gift_fee = 50 if order.gift_wrap else 0
        subtotal = order.total_price - delivery_fee - gift_fee
        
        summary_data = [
            ['', 'Subtotal:', f"₹{subtotal}"],
            ['', 'Delivery Fees:', "FREE" if delivery_fee == 0 else f"₹{delivery_fee}"],
        ]
        if order.gift_wrap:
             summary_data.append(['', 'Gift Wrapping:', "₹50.00"])
        
        summary_data.append(['', 'TOTAL AMOUNT:', f"₹{order.total_price}"])

        summary_table = Table(summary_data, colWidths=[100*mm, 35*mm, 35*mm])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (-2, -1), (-1, -1), 12),
            ('TEXTCOLOR', (-2, -1), (-1, -1), navy),
            ('TOPPADDING', (-2, -1), (-1, -1), 10),
        ]))
        elements.append(summary_table)

        # Footer
        elements.append(Spacer(1, 30*mm))
        elements.append(Paragraph("Thank you for supporting our handmade business ❤️", ParagraphStyle('Footer', parent=normal_style, alignment=1, fontSize=12, fontName='Helvetica-Bold')))
        elements.append(Spacer(1, 5*mm))
        elements.append(Paragraph("Please share your order screenshot via Instagram/WhatsApp after placing order for faster processing.", ParagraphStyle('Note', parent=normal_style, alignment=1, fontSize=8, textColor=mauve)))

        doc.build(elements)
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="TF_Invoice_{order.id}.pdf"'
        return response
    except Exception as e:
        print(f"ERROR: {str(e)}")
        messages.error(request, "Invoice generation failed.")
        return redirect('order_history')

def download_all_images(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # Check if user is staff or the order belongs to them
    if not request.user.is_staff and order.user != request.user:
        return HttpResponse("Unauthorized", status=401)
        
    images = order.images.all()

    if not images:
        messages.info(request, "No custom images found for this order.")
        return redirect('order_detail', id=order_id)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for img in images:
            if img.image:
                file_name = os.path.basename(img.image.name)
                zip_file.writestr(file_name, img.image.read())

    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename=order_{order_id}_images.zip'
    return response

@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        wishlist_item.delete()
        messages.info(request, f"Removed {product.name} from wishlist.")
    else:
        messages.success(request, f"Added {product.name} to wishlist.")
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'shop/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code')
        cart = get_or_create_cart(request)
        try:
            coupon = Coupon.objects.get(code__iexact=code, active=True)
            cart.coupon = coupon
            cart.save()
            messages.success(request, f"Coupon '{code}' applied! You got {coupon.discount}% off.")
        except Coupon.DoesNotExist:
            messages.error(request, "Invalid or expired coupon.")
    return redirect('cart')

@login_required
def add_review(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        messages.success(request, "Thank you for your review!")
    return redirect('product_detail', pk=product_id)

# ----------------- CUSTOM ADMIN DASHBOARD VIEWS -----------------

def admin_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_login')
    return _wrapped_view_func

def admin_login(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff or user.is_superuser:
                login(request, user)
                return redirect('admin_home')
            else:
                messages.error(request, "Access denied. Only admins can access this dashboard.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'admin_dashboard/login.html', {'form': form})

def admin_logout(request):
    logout(request)
    return redirect('admin_login')

@admin_required
def admin_home(request):
    from django.utils import timezone
    from datetime import timedelta
    
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    # Today's Orders & Revenue
    today_orders_qs = Order.objects.filter(created_at__date=today)
    today_orders_count = today_orders_qs.count()
    today_revenue = today_orders_qs.exclude(status='Cancelled').aggregate(Sum('total_price'))['total_price__sum'] or 0

    # Monthly Revenue
    monthly_revenue = Order.objects.filter(created_at__date__gte=start_of_month).exclude(status='Cancelled').aggregate(Sum('total_price'))['total_price__sum'] or 0

    # Order status counters
    pending_orders = Order.objects.filter(status='Pending').count()
    processing_orders = Order.objects.filter(status='Processing').count()
    ready_make_orders = Order.objects.filter(status='Ready to Make').count()
    ready_pack_orders = Order.objects.filter(status='Ready to Pack').count()
    shipped_orders = Order.objects.filter(status='Shipped').count()
    delivered_orders = Order.objects.filter(status='Delivered').count()
    cancelled_orders = Order.objects.filter(status='Cancelled').count()

    # Customer & Product counters
    total_customers = User.objects.filter(is_staff=False).count()
    total_products = Product.objects.count()

    # Recent Orders & Payments
    recent_orders = Order.objects.all().order_by('-created_at')[:8]
    recent_payments = Order.objects.exclude(status='Cancelled').order_by('-created_at')[:8]

    # Top Selling Products (ordered by sum of quantity)
    top_selling = OrderItem.objects.values('product__name', 'product__image').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:5]

    # Low Performing Products
    low_performing = Product.objects.annotate(total_sold=Sum('orderitem__quantity')).order_by('total_sold')[:5]

    # Graph Data: Last 7 days orders & revenue
    graph_labels = []
    graph_orders = []
    graph_revenue = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        graph_labels.append(date.strftime('%b %d'))
        day_orders = Order.objects.filter(created_at__date=date)
        graph_orders.append(day_orders.count())
        day_rev = day_orders.exclude(status='Cancelled').aggregate(Sum('total_price'))['total_price__sum'] or 0
        graph_revenue.append(float(day_rev))

    context = {
        'today_orders_count': today_orders_count,
        'today_revenue': today_revenue,
        'monthly_revenue': monthly_revenue,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'ready_make_orders': ready_make_orders,
        'ready_pack_orders': ready_pack_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'total_customers': total_customers,
        'total_products': total_products,
        'recent_orders': recent_orders,
        'recent_payments': recent_payments,
        'top_selling': top_selling,
        'low_performing': low_performing,
        'graph_labels': graph_labels,
        'graph_orders': graph_orders,
        'graph_revenue': graph_revenue,
    }
    return render(request, 'admin_dashboard/home.html', context)

@admin_required
def admin_orders(request):
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    
    orders = Order.objects.all().order_by('-created_at')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    if search_query:
        orders = orders.filter(
            Q(id__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )
        
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'search_query': search_query,
        'STATUS_CHOICES': Order.STATUS_CHOICES
    }
    return render(request, 'admin_dashboard/orders.html', context)

@admin_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        expected_delivery = request.POST.get('expected_delivery')
        courier_name = request.POST.get('courier_name')
        tracking_id = request.POST.get('tracking_id')
        status = request.POST.get('status')
        
        if expected_delivery:
            order.expected_delivery = expected_delivery
        if courier_name:
            order.courier_name = courier_name
        if tracking_id:
            order.tracking_id = tracking_id
        if status:
            order.status = status
        order.save()
        messages.success(request, "Order details updated successfully.")
        return redirect('admin_order_detail', order_id=order.id)
        
    context = {
        'order': order,
        'STATUS_CHOICES': Order.STATUS_CHOICES
    }
    return render(request, 'admin_dashboard/order_detail.html', context)

@admin_required
def update_checklist(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        data = json.loads(request.body)
        field = data.get('field')
        value = data.get('value', False)
        
        if hasattr(order, field):
            setattr(order, field, value)
            order.save()
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@admin_required
def admin_products(request):
    products = Product.objects.all().order_by('-created')
    return render(request, 'admin_dashboard/products.html', {'products': products})

from django import forms

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'price', 'original_price', 
            'image', 'external_image_url', 'available', 'is_featured',
            'enable_customization', 'customization_label', 
            'enable_size_selection', 'enable_name_pricing', 
            'enable_photo_upload', 'enable_custom_message', 
            'enable_gift_option', 'enable_thread_color', 
            'enable_frame_color', 'enable_led_option',
            'included_letters', 'extra_letter_price',
            'is_bestseller', 'is_new_arrival'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

@admin_required
def admin_product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product {product.name} created successfully.")
            return redirect('admin_products')
    else:
        form = ProductForm()
    return render(request, 'admin_dashboard/product_form.html', {'form': form, 'action': 'Add'})

@admin_required
def admin_product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product {product.name} updated successfully.")
            return redirect('admin_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'admin_dashboard/product_form.html', {'form': form, 'action': 'Edit', 'product': product})

@admin_required
def admin_product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Product deleted successfully.")
    return redirect('admin_products')

@admin_required
def admin_customers(request):
    customers = User.objects.filter(is_staff=False).annotate(
        order_count=Count('orders', distinct=True),
        total_spent=Sum('orders__total_price')
    )
    return render(request, 'admin_dashboard/customers.html', {'customers': customers})

@admin_required
def admin_customer_detail(request, customer_id):
    customer = get_object_or_404(User, id=customer_id)
    orders = customer.orders.all().order_by('-created_at')
    addresses = customer.addresses.all()
    wishlist_items = customer.wishlist.all()
    
    context = {
        'customer': customer,
        'orders': orders,
        'addresses': addresses,
        'wishlist_items': wishlist_items
    }
    return render(request, 'admin_dashboard/customer_detail.html', context)

@admin_required
def admin_payments(request):
    orders = Order.objects.exclude(status='Cancelled').order_by('-created_at')
    return render(request, 'admin_dashboard/payments.html', {'orders': orders})

@admin_required
def admin_settings(request):
    settings_obj, created = BusinessSettings.objects.get_or_create(id=1)
    if request.method == 'POST':
        settings_obj.shipping_charges = request.POST.get('shipping_charges', 0)
        settings_obj.production_time = request.POST.get('production_time', '3-7 Business Days')
        settings_obj.contact_email = request.POST.get('contact_email', '')
        settings_obj.contact_phone = request.POST.get('contact_phone', '')
        settings_obj.gpay_upi_id = request.POST.get('gpay_upi_id', '')
        settings_obj.phonepe_upi_id = request.POST.get('phonepe_upi_id', '')
        settings_obj.instagram_url = request.POST.get('instagram_url', '')
        settings_obj.pinterest_url = request.POST.get('pinterest_url', '')
        
        if 'logo' in request.FILES:
            settings_obj.logo = request.FILES['logo']
        if 'banner' in request.FILES:
            settings_obj.banner = request.FILES['banner']
            
        settings_obj.save()
        messages.success(request, "Settings updated successfully.")
        return redirect('admin_settings')
        
    return render(request, 'admin_dashboard/settings.html', {'settings': settings_obj})

import csv
from django.http import JsonResponse, HttpResponse
import json

@admin_required
def admin_reports(request):
    return render(request, 'admin_dashboard/reports.html')

@admin_required
def export_orders_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Customer', 'Mobile', 'Status', 'Total Price', 'Date'])
    
    for order in Order.objects.all().order_by('-created_at'):
        writer.writerow([
            order.id, order.full_name, order.phone_number, 
            order.status, f"R {order.total_price}", 
            order.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    return response

@admin_required
def export_customers_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="customers_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Username', 'Name', 'Email', 'Total Orders', 'Total Spent'])
    
    customers = User.objects.filter(is_staff=False).annotate(
        order_count=Count('orders', distinct=True),
        total_spent=Sum('orders__total_price')
    )
    for customer in customers:
        writer.writerow([
            customer.username, f"{customer.first_name} {customer.last_name}", 
            customer.email, customer.order_count, 
            f"R {customer.total_spent or 0}"
        ])
    return response
    
@admin_required
def export_orders_pdf(request):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'ReportTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#0C2C47'), 
        spaceAfter=15
    )
    elements.append(Paragraph("ThreadFusion Business Reports - Orders", title_style))
    elements.append(Spacer(1, 10))
    
    table_data = [['ID', 'Customer', 'Status', 'Total', 'Date']]
    for order in Order.objects.all().order_by('-created_at'):
        table_data.append([
            str(order.id),
            order.full_name,
            order.status,
            f"Rs {order.total_price}",
            order.created_at.strftime('%Y-%m-%d')
        ])
        
    t = Table(table_data, colWidths=[20*mm, 50*mm, 35*mm, 35*mm, 40*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0C2C47')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9F9F9')])
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="orders_report.pdf"'
    return response

# ----------------- CUSTOM CUSTOMER DASHBOARD VIEWS -----------------

@login_required
def customer_dashboard(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    addresses = Address.objects.filter(user=request.user)
    reviews = Review.objects.filter(product__orderitem__order__user=request.user).distinct() # Fetch user product reviews
    
    context = {
        'orders': orders,
        'wishlist_items': wishlist_items,
        'addresses': addresses,
        'reviews': reviews,
    }
    return render(request, 'dashboard/home.html', context)
