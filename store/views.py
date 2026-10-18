
from django.shortcuts import render, get_object_or_404,redirect
from .models import Product, Category
from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_POST
from decimal import Decimal
from .models import Product, Order, OrderItem


def home(request):
    products = Product.objects.all()
    categories = Category.objects.all()

    return render(request, 'home.html', {
        'products': products,
        'categories': categories,
    })


def category_products(request, category_id):
    categories = Category.objects.all()

    selected_category = get_object_or_404(
        Category,
        id=category_id
    )

    products = Product.objects.filter(
        category=selected_category
    )

    return render(request, 'home.html', {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
    })
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    return render(request, 'product_detail.html', {
        'product': product
    })
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    product_id = str(product.id)

    if product.stock > 0:
        current_quantity = cart.get(product_id, 0)

        if current_quantity < product.stock:
            cart[product_id] = current_quantity + 1

    request.session['cart'] = cart
    return redirect('cart')


def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=int(product_id))

        quantity = min(quantity, product.stock)

        if quantity <= 0:
            continue

        subtotal = product.price * quantity
        total += subtotal

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total,
    })


def update_cart(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        product = get_object_or_404(Product, id=product_id)
        key = str(product_id)

        if key in cart:
            action = request.POST.get('action')

            if action == 'increase' and cart[key] < product.stock:
                cart[key] += 1

            elif action == 'decrease':
                cart[key] -= 1

                if cart[key] <= 0:
                    del cart[key]

        request.session['cart'] = cart

    return redirect('cart')


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart.pop(str(product_id), None)
    request.session['cart'] = cart

    return redirect('cart')
def checkout_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = Decimal('0.00')

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=int(product_id))

        if product.stock <= 0:
            continue

        quantity = min(int(quantity), product.stock)

        if quantity <= 0:
            continue

        subtotal = product.price * quantity
        total += subtotal

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })

    if not cart_items:
        messages.error(request, 'Your cart is empty or products are unavailable.')
        return redirect('cart')

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total': total,
    })


@require_POST
def place_order(request):
    cart = request.session.get('cart', {})

    customer_name = request.POST.get('customer_name', '').strip()
    phone = request.POST.get('phone', '').strip()
    address = request.POST.get('address', '').strip()

    if not customer_name or not phone or not address:
        messages.error(request, 'Please fill in all the fields.')
        return redirect('checkout')

    if not phone.isdigit() or not 10 <= len(phone) <= 15:
        messages.error(request, 'Enter a valid phone number.')
        return redirect('checkout')

    try:
        with transaction.atomic():
            total = Decimal('0.00')
            order_lines = []

            for product_id, quantity in cart.items():
                product = Product.objects.select_for_update().get(
                    id=int(product_id)
                )
                quantity = int(quantity)

                if quantity <= 0 or product.stock < quantity:
                    raise ValueError(
                        f'Insufficient stock for {product.name}.'
                    )

                total += product.price * quantity
                order_lines.append((product, quantity))

            if not order_lines:
                raise ValueError('Your cart is empty.')

            order = Order.objects.create(
                customer_name=customer_name,
                phone=phone,
                address=address,
                total_amount=total,
            )

            for product, quantity in order_lines:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price,
                )

                product.stock -= quantity
                product.save(update_fields=['stock'])

    except (Product.DoesNotExist, ValueError) as error:
        messages.error(request, str(error))
        return redirect('cart')

    request.session['cart'] = {}

    return render(request, 'order_success.html', {
        'order': order,
    })