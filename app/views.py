# project-root/app/views.py
"""
Views for handling web requests and business logic
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Product, Transaction
from .utils import verify_firebase_token, initiate_stk_push
import json
from django.contrib.auth import get_user_model

# Authentication Views
def custom_login(request):
    """Handle user login"""
    if request.method == 'POST':
        # Get form data
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # Login successful
            login(request, user)
            return redirect('dashboard')
        else:
            # Invalid credentials
            messages.error(request, 'Invalid email or password')
    
    # Render login form
    return render(request, 'auth/login.html')

def custom_signup(request):
    """Handle user registration"""
    if request.method == 'POST':
        # Get form data
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        # Validate passwords match
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'auth/signup.html')
        
        try:
            # Create new user
            User = get_user_model()
            user = User.objects.create_user(
                username=email, 
                email=email, 
                password=password
            )
            user.save()
            
            # Authenticate and log in new user
            user = authenticate(username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
        except Exception as e:
            # Handle registration error
            messages.error(request, f'Error creating account: {str(e)}')
    
    # Render registration form
    return render(request, 'auth/signup.html')

def custom_logout(request):
    """Handle user logout"""
    logout(request)
    return redirect('home')

def forgot_password(request):
    """Handle password reset requests"""
    if request.method == 'POST':
        # In production: Implement Firebase password reset
        email = request.POST.get('email')
        messages.success(request, 'Password reset link sent to your email')
        return redirect('login')
    return render(request, 'auth/forgot_password.html')

# Main Application Views
def home(request):
    """Home page view"""
    # Get first 4 products to display
    products = Product.objects.all()[:4]
    return render(request, 'home.html', {'products': products})

@login_required
def dashboard(request):
    """User dashboard view"""
    # Get user's products and transactions
    products = Product.objects.filter(owner=request.user)
    transactions = Transaction.objects.filter(product__owner=request.user)
    
    return render(request, 'dashboard.html', {
        'products': products,
        'transactions': transactions
    })

@login_required
def product_create(request):
    """Create new product"""
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        
        # Create new product
        product = Product.objects.create(
            name=name,
            description=description,
            price=price,
            owner=request.user
        )
        messages.success(request, 'Product created successfully')
        return redirect('dashboard')
    
    # Render product creation form
    return render(request, 'product_form.html')

@login_required
def product_update(request, pk):
    """Update existing product"""
    # Get product or return 404
    product = get_object_or_404(Product, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        # Update product with new data
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.save()
        messages.success(request, 'Product updated successfully')
        return redirect('dashboard')
    
    # Render product edit form
    return render(request, 'product_form.html', {'product': product})

@login_required
def product_delete(request, pk):
    """Delete product"""
    # Get product or return 404
    product = get_object_or_404(Product, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        # Delete product
        product.delete()
        messages.success(request, 'Product deleted successfully')
    
    return redirect('dashboard')

@login_required
def initiate_payment(request, product_id):
    """Initiate M-Pesa payment"""
    # Get product or return 404
    product = get_object_or_404(Product, pk=product_id)
    
    if request.method == 'POST':
        # Get phone number from form
        phone = request.POST.get('phone')
        
        # Initiate M-Pesa payment
        response = initiate_stk_push(
            phone=phone,
            amount=str(product.price),
            reference=f"PROD-{product.id}"
        )
        
        # Handle response
        if response and response.get('ResponseCode') == '0':
            # Create transaction record
            Transaction.objects.create(
                product=product,
                amount=product.price,
                phone_number=phone,
                status='pending'
            )
            messages.success(request, 'Payment initiated! Check your phone to complete')
        else:
            # Handle payment initiation failure
            error_message = response.get('errorMessage') if response else 'Unknown error'
            messages.error(request, f'Failed to initiate payment: {error_message}')
        
        return redirect('dashboard')
    
    # Render payment initiation form
    return render(request, 'payment.html', {'product': product})

# API View for M-Pesa Callback
def mpesa_callback(request):
    """Handle M-Pesa payment callback"""
    if request.method == 'POST':
        try:
            # Parse JSON data from callback
            data = json.loads(request.body)
            result = data.get('Body', {}).get('stkCallback', {})
            
            # Check if payment was successful
            if result.get('ResultCode') == 0:
                # Extract transaction details
                metadata = result.get('CallbackMetadata', {}).get('Item', [])
                
                # Find relevant transaction details
                amount = next((item['Value'] for item in metadata if item['Name'] == 'Amount'), None)
                mpesa_code = next((item['Value'] for item in metadata if item['Name'] == 'MpesaReceiptNumber'), None)
                phone = next((item['Value'] for item in metadata if item['Name'] == 'PhoneNumber'), None)
                
                # Update transaction status
                if mpesa_code and phone:
                    # Find matching transaction (using last 9 digits of phone)
                    transaction = Transaction.objects.filter(
                        phone_number=phone[-9:],  # Last 9 digits
                        amount=amount,
                        status='pending'
                    ).first()
                    
                    if transaction:
                        # Update transaction as successful
                        transaction.mpesa_code = mpesa_code
                        transaction.status = 'success'
                        transaction.save()
            
            # Return success response to M-Pesa
            return JsonResponse({'status': 'success'})
        except Exception as e:
            # Log error and return error response
            print(f"Error processing callback: {str(e)}")
            return JsonResponse({'status': 'error'}, status=400)
    
    # Return method not allowed for non-POST requests
    return JsonResponse({'status': 'invalid method'}, status=405)