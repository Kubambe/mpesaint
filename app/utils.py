# project-root/app/utils.py
"""
Utility functions for Firebase authentication and M-Pesa integration
"""
import os
import base64
import datetime
import requests
import firebase_admin
from firebase_admin import credentials, auth
from django.conf import settings
from django.contrib.auth import get_user_model

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase app with service account credentials"""
    try:
        # Load credentials from specified path
        cred = credentials.Certificate(settings.FIREBASE_CERTIFICATE_PATH)
        # Initialize Firebase app
        firebase_admin.initialize_app(cred)
    except ValueError:
        # Firebase already initialized
        pass

# Verify Firebase ID token
def verify_firebase_token(token):
    """Verify Firebase ID token and return decoded claims"""
    initialize_firebase()  # Ensure Firebase is initialized
    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except (ValueError, auth.InvalidIdTokenError, auth.ExpiredIdTokenError):
        # Token is invalid or expired
        return None

# Get M-Pesa access token
def get_mpesa_access_token():
    """Obtain access token from M-Pesa OAuth API"""
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    
    # Make request to M-Pesa OAuth endpoint
    response = requests.get(
        api_url, 
        auth=(consumer_key, consumer_secret),  # Basic authentication
        headers={'Content-Type': 'application/json'}
    )
    
    # Return access token if successful
    if response.status_code == 200:
        return response.json().get('access_token')
    return None

# Initiate M-Pesa STK push
def initiate_stk_push(phone, amount, reference):
    """Initiate M-Pesa STK push payment request"""
    # Get access token
    access_token = get_mpesa_access_token()
    if not access_token:
        return None  # Failed to get token
        
    # Load M-Pesa credentials from settings
    business_short_code = settings.MPESA_BUSINESS_SHORT_CODE
    passkey = settings.MPESA_PASSKEY
    callback_url = settings.MPESA_CALLBACK_URL
    
    # Generate timestamp and password
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(
        f"{business_short_code}{passkey}{timestamp}".encode()
    ).decode()
    
    # Format phone number to 254 format
    phone = f"254{phone[-9:]}"  # Convert 07XXXXXXXX to 2547XXXXXXXX
    
    # Prepare request headers
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Prepare request payload
    payload = {
        "BusinessShortCode": business_short_code,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,  # Customer phone
        "PartyB": business_short_code,  # Business shortcode
        "PhoneNumber": phone,  # Customer phone
        "CallBackURL": callback_url,  # Callback endpoint
        "AccountReference": reference,  # Payment reference
        "TransactionDesc": "Payment for goods"  # Transaction description
    }
    
    # Send STK push request
    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers=headers
    )
    
    return response.json()  # Return API response