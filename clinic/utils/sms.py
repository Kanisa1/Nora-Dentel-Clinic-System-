import os
import africastalking
from django.conf import settings

# Expect AFRICASTALKING_USERNAME and AFRICASTALKING_API_KEY in env or django settings
AT_USERNAME = getattr(settings, "AFRICASTALKING_USERNAME", os.getenv("AFRICASTALKING_USERNAME", "sandbox"))
AT_API_KEY = getattr(settings, "AFRICASTALKING_API_KEY", os.getenv("AFRICASTALKING_API_KEY", None))

# initialize once
if not AT_API_KEY:
    print("Warning: AfricasTalking API key not configured. SMS won't be sent.")
else:
    africastalking.initialize(AT_USERNAME, AT_API_KEY)
    sms_service = africastalking.SMS

def format_phone_number(phone: str) -> str:
    """
    Format phone number to international format for AfricasTalking
    Expects Rwandan numbers, formats as +250xxxxxxxxx
    """
    # Remove any spaces, dashes, or special characters
    phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    # If already starts with +, return as is
    if phone.startswith('+'):
        return phone
    
    # If starts with 0, replace with +250
    if phone.startswith('0'):
        return '+250' + phone[1:]
    
    # If 10 digits without leading 0, assume Rwandan number
    if len(phone) == 10 and phone.isdigit():
        return '+250' + phone
    
    # If already has country code 250 without +
    if phone.startswith('250'):
        return '+' + phone
    
    # Return as-is if we can't determine format
    return '+' + phone if not phone.startswith('+') else phone

def send_sms(message: str, to: list):
    """
    to: list of phone numbers (local or international format)
    Automatically formats to international format for AfricasTalking
    """
    if not AT_API_KEY:
        raise RuntimeError("Africastalking API key not configured.")
    
    # Format all phone numbers to international format
    formatted_numbers = [format_phone_number(phone) for phone in to]
    
    try:
        response = sms_service.send(message, formatted_numbers)
        return response
    except Exception as e:
        # Log but don't crash - SMS is not critical
        print(f"Warning: Failed to send SMS: {str(e)}")
        return None
