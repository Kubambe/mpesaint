# project-root/app/models.py
"""
Database models for the application
"""
from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    """Product model for CRUD operations"""
    name = models.CharField(max_length=200)  # Product name
    description = models.TextField()  # Detailed description
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price in Ksh
    created_at = models.DateTimeField(auto_now_add=True)  # Creation timestamp
    updated_at = models.DateTimeField(auto_now=True)  # Last update timestamp
    owner = models.ForeignKey(User, on_delete=models.CASCADE)  # Product owner (user)

    def __str__(self):
        """String representation of product"""
        return self.name

class Transaction(models.Model):
    """Transaction model for M-Pesa payments"""
    # Status choices for transaction
    STATUS_CHOICES = [
        ('pending', 'Pending'),  # Payment initiated but not confirmed
        ('success', 'Success'),  # Payment successful
        ('failed', 'Failed'),  # Payment failed
    ]
    
    # Relationships and fields
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Related product
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Transaction amount
    phone_number = models.CharField(max_length=15)  # Customer phone number
    mpesa_code = models.CharField(max_length=50, blank=True, null=True)  # M-Pesa transaction code
    status = models.CharField(  # Current transaction status
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)  # Creation timestamp

    def __str__(self):
        """String representation of transaction"""
        return f"{self.product} - {self.amount}"