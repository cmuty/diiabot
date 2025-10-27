"""
Upload IPA file to Cloudinary (run once)
"""
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Cloudinary
cloudinary_url = os.getenv("CLOUDINARY_URL")
if not cloudinary_url:
    raise RuntimeError("CLOUDINARY_URL is not configured")

cloudinary.config(
    cloudinary_url=cloudinary_url,
    secure=True,
)

# Path to IPA file (update this path)
IPA_PATH = "uploads/ipa/MaijeDiia.ipa"

# Check if file exists
if not os.path.exists(IPA_PATH):
    print(f"❌ File not found: {IPA_PATH}")
    print("Please update IPA_PATH in this script to point to your .ipa file")
    exit(1)

print(f"📤 Uploading {IPA_PATH} to Cloudinary...")
print(f"⏳ This may take a few minutes...")

try:
    # Upload IPA file to Cloudinary
    result = cloudinary.uploader.upload(
        IPA_PATH,
        resource_type="raw",  # For non-media files
        public_id="maije-diia-app",  # Custom name
        folder="diia",  # Optional folder
        overwrite=True
    )
    
    secure_url = result['secure_url']
    
    print(f"\n✅ Upload successful!")
    print(f"\n📋 Add this to your .env file on Render:")
    print(f"IPA_CLOUDINARY_URL={secure_url}")
    print(f"\n🔗 Direct download link:")
    print(f"{secure_url}")
    
except Exception as e:
    print(f"❌ Upload failed: {e}")

