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
]
