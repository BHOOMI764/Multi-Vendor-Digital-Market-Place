from django.shortcuts import render,get_object_or_404,reverse,redirect
from .models import Product,OrderDetail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse,HttpResponseNotFound
import stripe,json
from .forms import ProductForm,UserRegistrationForm
from django.db.models import Sum
import datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
# Create your views here.
def index(request):
    products = Product.objects.all()
    
    return render(request,'myapp/index.html',{'products':products})

def detail(request,id):
    product = Product.objects.get(id=id)
    stripe_publishable_key = settings.STRIPE_PUBLISHABLE_KEY
    return render(request, 'myapp/detail.html',{'product':product,'stripe_publishable_key':stripe_publishable_key})
    
    
@csrf_exempt
def create_checkout_session(request,id):
    request_data = json.loads(request.body)
    product = Product.objects.get(id=id)
    stripe.api_key = settings.STRIPE_SECRET_KEY
    checkout_session = stripe.checkout.Session.create(
        customer_email = request_data['email'],
        payment_method_types = ['card'],
        line_items=[
            {
                'price_data':{
                    'currency':'usd',
                    'product_data':{
                        'name':product.name,
                    },
                    'unit_amount':int(product.price * 100)
                },
                'quantity':1,
            }
        ],
        mode='payment',
        success_url = request.build_absolute_uri(reverse('success')) +
        "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url = request.build_absolute_uri(reverse('failed')),
        
    )
    
    # Stripe Checkout Session may not include `payment_intent` immediately.
    # Store the session id as a fallback so the order can be looked up later.
    order = OrderDetail()
    order.customer_email = request_data['email']
    order.product = product
    spi = checkout_session.get('payment_intent') if isinstance(checkout_session, dict) else getattr(checkout_session, 'payment_intent', None)
    if not spi:
        # fallback to session id
        spi = checkout_session.get('id') if isinstance(checkout_session, dict) else getattr(checkout_session, 'id', None)
    order.stripe_payment_intent = spi
    order.amount = int(product.price)
    order.save()
    
    return JsonResponse({'sessionId':checkout_session.id})
    
def payment_success_view(request):
    session_id = request.GET.get('session_id')
    if session_id is None:
        return HttpResponseNotFound()
    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.retrieve(session_id)
    # Try to find order by payment_intent first, then by session id (stored as fallback).
    payment_intent = getattr(session, 'payment_intent', None)
    order = None
    if payment_intent:
        try:
            order = OrderDetail.objects.get(stripe_payment_intent=payment_intent)
        except OrderDetail.DoesNotExist:
            order = None
    if not order:
        session_key = getattr(session, 'id', None)
        order = get_object_or_404(OrderDetail, stripe_payment_intent=session_key)
    order.has_paid=True
    # updating sales stats for a product
    product = Product.objects.get(id=order.product.id)
    product.total_sales_amount = product.total_sales_amount + int(product.price)
    product.total_sales = product.total_sales + 1
    product.save()
    # updating sales stats for a product
    order.save()
    
    return render(request,'myapp/payment_success.html',{'order':order})
    
def payment_failed_view(request):
    return render(request,'myapp/failed.html')

@login_required
def create_product(request):
    if request.method =='POST':
        product_form = ProductForm(request.POST,request.FILES)
        if product_form.is_valid():
            new_product = product_form.save(commit=False)
            new_product.seller = request.user
            new_product.save()
            return redirect('index')
        
    product_form = ProductForm()
    return render(request, 'myapp/create_product.html',{'product_form':product_form})

@login_required
def product_edit(request,id):
    product = Product.objects.get(id=id)
    if product.seller != request.user:
        return redirect('invalid')
    
    product_form = ProductForm(request.POST or None,request.FILES or None,instance=product)
    if request.method=='POST':
        if product_form.is_valid():
            product_form.save()
            return redirect('index')
    return render(request,'myapp/product_edit.html',{'product_form':product_form,'product':product})


@login_required
def product_delete(request,id):
    product = Product.objects.get(id=id)
    if product.seller != request.user:
        return redirect('invalid')
    if request.method =='POST':
        product.delete()
        return redirect('index')
    return render(request, 'myapp/delete.html',{'product':product})

@login_required
def dashboard(request):
    products = Product.objects.filter(seller=request.user)
    return render(request, 'myapp/dashboard.html',{'products':products})

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            return redirect('index')
    else:
        user_form = UserRegistrationForm()
    return render(request,'myapp/register.html',{'user_form':user_form})

def invalid(request):
    return render(request, 'myapp/invalid.html')

def my_purchases(request):
    if not request.user.is_authenticated:
        return redirect('login')
    orders = OrderDetail.objects.filter(customer_email=request.user.email)
    return render(request, 'myapp/purchases.html',{'orders':orders})

def sales(request):
    if not request.user.is_authenticated:
        return redirect('login')
    orders = OrderDetail.objects.filter(product__seller=request.user)
    total_sales = orders.aggregate(Sum('amount'))
    print(total_sales)
    
    #365 day sales sum
    last_year = datetime.date.today() - datetime.timedelta(days=365)
    data = OrderDetail.objects.filter(product__seller=request.user,created_on__gt=last_year)
    yearly_sales = data.aggregate(Sum('amount'))
    
    #30 day sales sum
    last_month = datetime.date.today() - datetime.timedelta(days=30)
    data = OrderDetail.objects.filter(product__seller=request.user,created_on__gt=last_month)
    monthly_sales = data.aggregate(Sum('amount'))
    
    #7 day sales sum
    last_week = datetime.date.today() - datetime.timedelta(days=7)
    data = OrderDetail.objects.filter(product__seller=request.user,created_on__gt=last_week)
    weekly_sales = data.aggregate(Sum('amount'))
    
    #Everday sum for the past 30 days
    daily_sales_sums = OrderDetail.objects.filter(product__seller=request.user).values('created_on__date').order_by('created_on__date').annotate(sum=Sum('amount'))
    
    
    
    product_sales_sums = OrderDetail.objects.filter(product__seller=request.user).values('product__name').order_by('product__name').annotate(sum=Sum('amount'))
    print(product_sales_sums)

    return render(request, 'myapp/sales.html',{'total_sales':total_sales,'yearly_sales':yearly_sales,'monthly_sales':monthly_sales,'weekly_sales':weekly_sales,'daily_sales_sums':daily_sales_sums,'product_sales_sums':product_sales_sums})

def logout_view(request):
    logout(request)
    return redirect('index')