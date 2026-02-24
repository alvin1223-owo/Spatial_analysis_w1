#!/usr/bin/env python3

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test if API key is loaded
api_key = os.getenv('CWA_API_KEY')
print(f"CWA_API_KEY loaded: {api_key is not None}")
if api_key:
    print(f"API Key: {api_key}")
else:
    print("API Key not found in .env file")
