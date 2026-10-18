from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path(
        'category/<int:category_id>/',
        views.category_products,
        name='category_products'
    ),
    path(
        'product/<int:product_id>/',
        views.product_detail,
        name='product_detail'
    ),
path('cart/', views.cart_view, name='cart'),
path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
path('cart/update/<int:product_id>/', views.update_cart,name='update_cart'),
path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
path('checkout/', views.checkout_view, name='checkout'),
path('place-order/', views.place_order, name='place_order'),
]