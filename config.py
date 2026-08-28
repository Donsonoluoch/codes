import os
from urllib.parse import quote_plus # For URL encoding the company name

class Config:
    # config.py
    # ... other settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_super_secret_dev_key_if_not_set_in_env' # Use a stronger default for production
    # Business Central credentials
    BC_USER = os.getenv("BC_USER") # This is where it's supposed to be loaded.
    BC_PASS = os.getenv("BC_PASS")
    BC_USE_NTLM = os.getenv("BC_USE_NTLM", "False").lower() in ("1", "true", "yes")
    BC_VERIFY_TLS = os.getenv("BC_VERIFY_TLS", "True").lower() in ("1", "true", "yes") # If you use HTTPS for BC OData
   
    # Business Central OData Base Components (for ON-PREMISE)
    BC_SERVER_NAME = os.getenv("BC_SERVER_NAME", "localhost")
    BC_ODATA_PORT = os.getenv("BC_ODATA_PORT", "7048")
    BC_INSTANCE_NAME = os.getenv("BC_INSTANCE_NAME", "BC200")
    BC_COMPANY_NAME_ENCODED = quote_plus(os.getenv("BC_COMPANY_NAME", "Donson"))

    # Web Service names from the 'Web Services' page
    BC_STUDENT_API_SERVICE_NAME = os.getenv("BC_STUDENT_API_SERVICE_NAME")
    BC_USER_API_SERVICE_NAME = os.getenv("BC_USER_API_SERVICE_NAME")