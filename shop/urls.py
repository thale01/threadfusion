from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/add-address/', views.add_address, name='add_address'),
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_history, name='order_history'),
    path('order/<int:id>/', views.order_detail, name='order_detail'),
    path('customize/', views.customize_view, name='customize'),
    path('returns/', views.returns_view, name='returns'),
    path('contact/', views.contact_view, name='contact'),
    path('shipping/', views.shipping_view, name='shipping'),
    path('invoice/<int:order_id>/', views.generate_invoice, name='invoice'),
    path('download-images/<int:order_id>/', views.download_all_images, name='download_all_images'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('product/<int:product_id>/add-review/', views.add_review, name='add_review'),

    # Admin Dashboard Routes
    path('admin-dashboard/login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/logout/', views.admin_logout, name='admin_logout'),
    path('admin-dashboard/', views.admin_home, name='admin_home'),
    path('admin-dashboard/orders/', views.admin_orders, name='admin_orders'),
    path('admin-dashboard/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin-dashboard/orders/<int:order_id>/update-checklist/', views.update_checklist, name='update_checklist'),
    path('admin-dashboard/products/', views.admin_products, name='admin_products'),
    path('admin-dashboard/products/add/', views.admin_product_add, name='admin_product_add'),
    path('admin-dashboard/products/edit/<int:product_id>/', views.admin_product_edit, name='admin_product_edit'),
    path('admin-dashboard/products/delete/<int:product_id>/', views.admin_product_delete, name='admin_product_delete'),
    path('admin-dashboard/customers/', views.admin_customers, name='admin_customers'),
    path('admin-dashboard/customers/<int:customer_id>/', views.admin_customer_detail, name='admin_customer_detail'),
    path('admin-dashboard/payments/', views.admin_payments, name='admin_payments'),
    path('admin-dashboard/settings/', views.admin_settings, name='admin_settings'),
    path('admin-dashboard/reports/', views.admin_reports, name='admin_reports'),
    path('admin-dashboard/reports/orders/csv/', views.export_orders_csv, name='export_orders_csv'),
    path('admin-dashboard/reports/customers/csv/', views.export_customers_csv, name='export_customers_csv'),
    path('admin-dashboard/reports/orders/pdf/', views.export_orders_pdf, name='export_orders_pdf'),

    # Customer Dashboard Routes
    path('dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('buy-now/', views.add_to_cart, name='buy_now'),

    # Admin Product Sub-resources Managers
    path('admin-dashboard/products/<int:product_id>/sizes/save/', views.admin_product_size_save, name='admin_product_size_save'),
    path('admin-dashboard/products/<int:product_id>/sizes/delete/<int:size_id>/', views.admin_product_size_delete, name='admin_product_size_delete'),
    path('admin-dashboard/products/<int:product_id>/clips/save/', views.admin_product_clip_save, name='admin_product_clip_save'),
    path('admin-dashboard/products/<int:product_id>/clips/delete/<int:clip_id>/', views.admin_product_clip_delete, name='admin_product_clip_delete'),
    path('admin-dashboard/products/<int:product_id>/addons/save/', views.admin_product_addon_save, name='admin_product_addon_save'),
    path('admin-dashboard/products/<int:product_id>/addons/delete/<int:addon_id>/', views.admin_product_addon_delete, name='admin_product_addon_delete'),
]
