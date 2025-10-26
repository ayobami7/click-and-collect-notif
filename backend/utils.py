import random
import string
from datetime import datetime

def generate_barcode(prefix: str = "MNS") -> str:
    """
    Generate a unique barcode for collection
    Format: PREFIX-YYYYMMDD-RANDOM6
    Example: MNS-20251024-A3X9K2
    """
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{date_str}-{random_str}"

def generate_order_number() -> str:
    """
    Generate a unique order number
    Format: ORD-TIMESTAMP-RANDOM4
    Example: ORD-1698234567-A3X9
    """
    timestamp = int(datetime.now().timestamp())
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"ORD-{timestamp}-{random_str}"

def validate_barcode(barcode: str) -> bool:
    """
    Validate barcode format
    """
    if not barcode:
        return False
    
    parts = barcode.split('-')
    if len(parts) != 3:
        return False
    
    prefix, date, code = parts
    
    # Check prefix is alphabetic
    if not prefix.isalpha():
        return False
    
    # Check date is 8 digits
    if not date.isdigit() or len(date) != 8:
        return False
    
    # Check code is 6 alphanumeric characters
    if not code.isalnum() or len(code) != 6:
        return False
    
    return True