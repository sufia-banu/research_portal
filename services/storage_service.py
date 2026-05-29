"""
services/storage_service.py - Supabase storage integration for document uploads
"""
import uuid
import mimetypes
from database.connection import get_supabase_client, get_supabase_admin_client

BUCKET_NAME = "research_documents"
AVATAR_BUCKET = "profile_photos"

def upload_document(file_bytes: bytes, file_name: str, faculty_id: str) -> str | None:
    """Uploads a document to Supabase storage and returns the public URL."""
    try:
        # Ensure bucket exists first (using admin client)
        admin = get_supabase_admin_client()
        try:
            buckets = admin.storage.list_buckets()
            if not any(b.name == BUCKET_NAME for b in buckets):
                admin.storage.create_bucket(BUCKET_NAME, options={"public": True})
        except Exception as bucket_err:
            print(f"Bucket check/create error: {bucket_err}")

        client = get_supabase_client()
        ext = file_name.split('.')[-1] if '.' in file_name else 'pdf'
        unique_name = f"{faculty_id}/{uuid.uuid4()}.{ext}"
        mime_type, _ = mimetypes.guess_type(file_name)
        if not mime_type:
            mime_type = "application/octet-stream"

        # Use admin client for upload to bypass RLS issues for now
        res = admin.storage.from_(BUCKET_NAME).upload(
            unique_name,
            file_bytes,
            {"content-type": mime_type}
        )
        
        # Get public URL
        url_res = admin.storage.from_(BUCKET_NAME).get_public_url(unique_name)
        return url_res
    except Exception as e:
        print(f"Upload error: {e}")
        return None

def delete_document(document_url: str) -> bool:
    """Deletes a document from Supabase storage using its public URL."""
    try:
        if not document_url or BUCKET_NAME not in document_url:
            return False
            
        client = get_supabase_client()
        # Extract the path after the bucket name
        path = document_url.split(f"{BUCKET_NAME}/")[-1]
        
        # URL decode if needed
        import urllib.parse
        path = urllib.parse.unquote(path)
        
        client.storage.from_(BUCKET_NAME).remove([path])
        return True
    except Exception as e:
        print(f"Delete error: {e}")
        return False

def download_document_bytes(document_url: str) -> bytes | None:
    """Fetches document bytes using admin client for maximum reliability."""
    try:
        if not document_url or BUCKET_NAME not in document_url:
            return None
            
        client = get_supabase_admin_client()
        # Extract path from URL
        path = document_url.split(f"{BUCKET_NAME}/")[-1]
        import urllib.parse
        path = urllib.parse.unquote(path)
        
        res = client.storage.from_(BUCKET_NAME).download(path)
        return res
    except Exception as e:
        print(f"Admin download error: {e}")
        # Fallback to public request
        try:
            import requests
            response = requests.get(document_url)
            if response.status_code == 200:
                return response.content
        except:
            pass
        return None

def init_storage():
    """Ensures storage bucket exists and is public. Called on app startup."""
    try:
        admin = get_supabase_admin_client()
        # Ensure buckets exist
        for bname in [BUCKET_NAME, AVATAR_BUCKET]:
            try:
                admin.storage.get_bucket(bname)
            except:
                admin.storage.create_bucket(bname, options={"public": True})
            admin.storage.update_bucket(bname, options={"public": True})
    except Exception as e:
        print(f"Storage init error: {e}")

def upload_avatar(file_bytes: bytes, file_name: str, user_id: str) -> str | None:
    """Uploads a profile photo to Supabase storage."""
    try:
        admin = get_supabase_admin_client()
        # Ensure bucket exists
        try:
            buckets = admin.storage.list_buckets()
            if not any(b.name == AVATAR_BUCKET for b in buckets):
                admin.storage.create_bucket(AVATAR_BUCKET, options={"public": True})
        except: pass

        ext = file_name.split('.')[-1] if '.' in file_name else 'jpg'
        unique_name = f"{user_id}/photo_{uuid.uuid4().hex[:8]}.{ext}"
        
        # Delete old photos in user's folder
        try:
            files = admin.storage.from_(AVATAR_BUCKET).list(user_id)
            if files:
                admin.storage.from_(AVATAR_BUCKET).remove([f"{user_id}/{f['name']}" for f in files])
        except: pass

        # Upload new
        admin.storage.from_(AVATAR_BUCKET).upload(unique_name, file_bytes, {"content-type": f"image/{ext}"})
        return admin.storage.from_(AVATAR_BUCKET).get_public_url(unique_name)
    except Exception as e:
        print(f"Avatar upload error: {e}")
        return None
