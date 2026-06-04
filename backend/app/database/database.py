# =====================================================================
# Database Core Configuration - Plum OPD Adjudication
# =====================================================================

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load database configuration from environment
load_dotenv()

# Default MongoDB URL
# Note: In Render, .env is not present, so we use the Atlas URI as a fallback
ATLAS_URI = "mongodb+srv://rohithtnsp_db_user:7286027547@cluster0.xqz3vjx.mongodb.net/?appName=Cluster0"
MONGODB_URL = os.getenv("MONGODB_URL") or os.getenv("MONGO_URI") or ATLAS_URI

# Initialize MongoDB client
client = MongoClient(MONGODB_URL)

# Get reference to the Plum database
db = client.get_database("plum_db") if "mongodb+srv" in MONGODB_URL else client.plum_db
