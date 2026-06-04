# =====================================================================
# Database Core Configuration - Plum OPD Adjudication
# =====================================================================

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load database configuration from environment
load_dotenv()

# Default MongoDB URL
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")

# Initialize MongoDB client
client = MongoClient(MONGODB_URL)

# Get reference to the Plum database
db = client.get_database("plum_db") if "mongodb+srv" in MONGODB_URL else client.plum_db
