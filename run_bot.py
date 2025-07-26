#!/usr/bin/env python3
import os
import sys

# Set environment variables
os.environ['BOT_TOKEN'] = "7995053218:AAHjjk02qRGrVmrGy-i-xL4vXio7m8bwaE0"
os.environ['OWNER_ID'] = "1735522859" 
os.environ['LOG_GROUP_ID'] = "-1002878767296"

# Import and run main
from main import main

if __name__ == '__main__':
    main()