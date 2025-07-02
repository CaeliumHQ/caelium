import base64
import os
import secrets
import threading
import time
from pathlib import Path
import uuid

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from django.conf import settings
from django.db import transaction
from django.http import Http404, StreamingHttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cloud.google_drive import GoogleDriveStorage
from cloud.models import Directory, CloudFile, Tag, FileTag
from cloud.serializers import BreadcrumbSerializer, DirectorySerializer, FileSerializer, TagSerializer
from cloud.utils import check_type, extract_date_from_filename, get_directory_path


class FileCache:
    """Utility class for managing file caching"""

    # Default cache expiration time (24 hours in seconds)
    DEFAULT_EXPIRATION = 24 * 60 * 60

    # Maximum cache size (10GB by default)
    MAX_CACHE_SIZE = 10 * 1024 * 1024 * 1024

    def __init__(self):
        """Initialize the file cache directory"""
        # Create cache directory inside media folder
        self.cache_dir = Path(settings.MEDIA_ROOT) / "file_cache"
        self.cache_dir.mkdir(exist_ok=True, parents=True)

        # Create metadata file to track cache entries
        self.metadata_file = self.cache_dir / "metadata.txt"
        if not self.metadata_file.exists():
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                f.write("")
        # Start a background thread for cache cleanup
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """Start a background thread to periodically clean up expired cache entries"""

        def cleanup_task():
            while True:
                try:
                    self.cleanup_expired()
                    self.enforce_size_limit()
                except Exception as e:
                    print(f"Error in cache cleanup: {e}")
                # Run cleanup every hour
                time.sleep(3600)

        thread = threading.Thread(target=cleanup_task)
        thread.daemon = True
        thread.start()

    def get_cache_path(self, file_id):
        """Generate a cache file path for a file ID"""
        return self.cache_dir / f"{file_id}.cache"

    def file_exists(self, file_id):
        """Check if a file exists in the cache"""
        cache_path = self.get_cache_path(file_id)
        return cache_path.exists()

    def get_file_generator(self, file_id, chunk_size=10 * 1024 * 1024):
        """Get a generator that yields chunks from a cached file"""
        cache_path = self.get_cache_path(file_id)

        if not cache_path.exists():
            return None

        # Update the last access time
        self._update_access_time(file_id)

        # Stream the file in chunks
        with open(cache_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def save_file(self, file_id, content_generator, expiration=None):
        """Save a file to the cache from a generator"""
        cache_path = self.get_cache_path(file_id)
        tmp_path = cache_path.with_suffix(".tmp")

        # Write content to temporary file
        file_size = 0
        with open(tmp_path, "wb") as f:
            for chunk in content_generator:
                f.write(chunk)
                file_size += len(chunk)

        # Rename temp file to final cache file
        tmp_path.rename(cache_path)

        # Add metadata entry
        self._add_metadata(file_id, file_size, expiration or self.DEFAULT_EXPIRATION)

        # Check cache size and clean up if necessary
        self.enforce_size_limit()

        return file_size

    def invalidate(self, file_id):
        """Remove a file from the cache"""
        cache_path = self.get_cache_path(file_id)
        if cache_path.exists():
            cache_path.unlink()
        self._remove_metadata(file_id)

    def _add_metadata(self, file_id, size, expiration):
        """Add or update metadata for a cache entry"""
        now = int(time.time())
        expires_at = now + expiration

        # Read existing metadata
        entries = self._read_metadata()

        # Remove existing entry for this file_id if it exists
        entries = [e for e in entries if e.get("file_id") != str(file_id)]

        # Add new entry
        entries.append(
            {"file_id": str(file_id), "size": size, "created_at": now, "last_accessed": now, "expires_at": expires_at}
        )

        # Write updated metadata
        self._write_metadata(entries)

    def _update_access_time(self, file_id):
        """Update the last access time for a cached file"""
        entries = self._read_metadata()
        for entry in entries:
            if entry.get("file_id") == str(file_id):
                entry["last_accessed"] = int(time.time())
                break

        self._write_metadata(entries)

    def _remove_metadata(self, file_id):
        """Remove metadata for a file"""
        entries = self._read_metadata()
        entries = [e for e in entries if e.get("file_id") != str(file_id)]
        self._write_metadata(entries)

    def _read_metadata(self):
        """Read cache metadata from the metadata file"""
        if not self.metadata_file.exists():
            return []

        try:
            import json

            with open(self.metadata_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
                return []
        except Exception as e:
            print(f"Error reading cache metadata: {e}")
            return []

    def _write_metadata(self, entries):
        """Write cache metadata to the metadata file"""
        try:
            import json

            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(entries, f)
        except Exception as e:
            print(f"Error writing cache metadata: {e}")

    def cleanup_expired(self):
        """Remove expired cache entries"""
        now = int(time.time())
        entries = self._read_metadata()

        expired_entries = [e for e in entries if e.get("expires_at", 0) < now]
        remaining_entries = [e for e in entries if e.get("expires_at", 0) >= now]

        # Remove expired files
        for entry in expired_entries:
            file_id = entry.get("file_id")
            if file_id:
                cache_path = self.get_cache_path(file_id)
                if cache_path.exists():
                    try:
                        cache_path.unlink()
                    except Exception as e:
                        print(f"Error deleting expired cache file: {e}")

        # Update metadata
        self._write_metadata(remaining_entries)

    def enforce_size_limit(self):
        """Ensure the cache size is within limits, removing least recently used files if needed"""
        entries = self._read_metadata()

        # Calculate total size
        total_size = sum(e.get("size", 0) for e in entries)

        if total_size <= self.MAX_CACHE_SIZE:
            return

        # Sort by last accessed time (oldest first)
        entries.sort(key=lambda e: e.get("last_accessed", 0))

        # Remove files until we're under the limit
        removed_entries = []
        for entry in entries:
            if total_size <= self.MAX_CACHE_SIZE:
                break

            file_id = entry.get("file_id")
            file_size = entry.get("size", 0)

            if file_id:
                cache_path = self.get_cache_path(file_id)
                if cache_path.exists():
                    try:
                        cache_path.unlink()
                        total_size -= file_size
                        removed_entries.append(entry)
                    except Exception as e:
                        print(f"Error removing cache file during size enforcement: {e}")

        # Update metadata
        remaining_entries = [e for e in entries if e not in removed_entries]
        self._write_metadata(remaining_entries)


# Create a singleton instance of the file cache
file_cache = FileCache()


class FileDownloadView(APIView):
    """View for handling file downloads"""

    permission_classes = [IsAuthenticated]
    # Buffer size: 10MB chunks for streaming
    CHUNK_SIZE = 10 * 1024 * 1024

    def decrypt_chunk(self, chunk, key_bytes, iv_bytes, counter):
        """Decrypt a single chunk with AES-256 in CTR mode"""
        # CTR mode uses a counter that increases for each chunk
        # This allows us to decrypt chunks independently at any position
        cipher = Cipher(
            algorithms.AES(key_bytes), modes.CTR(iv_bytes + counter.to_bytes(4, byteorder="big")), backend=default_backend()
        )
        decryptor = cipher.decryptor()
        return decryptor.update(chunk) + decryptor.finalize()

    def decrypt_file_stream_from_local(self, file_obj):
        """Generator to stream decrypt file data in chunks from local file storage"""
        # Decode key and IV from base64
        key_bytes = base64.b64decode(file_obj.encryption_key)
        iv_bytes = base64.b64decode(file_obj.encryption_iv)

        # For CTR mode, we use a 12-byte nonce + 4-byte counter
        # Starting counter at 0
        counter = 0

        # Ensure the local file exists
        if not os.path.exists(file_obj.local_path):
            raise FileNotFoundError(f"Local file not found: {file_obj.local_path}")

        # Process file in chunks
        decrypted_chunks = []
        with open(file_obj.local_path, 'rb') as file_content:
            while True:
                chunk = file_content.read(self.CHUNK_SIZE)
                if not chunk:
                    break

                # Decrypt the chunk
                decrypted_chunk = self.decrypt_chunk(chunk, key_bytes, iv_bytes, counter)

                # Store for caching
                decrypted_chunks.append(decrypted_chunk)

                # Yield the chunk for streaming
                yield decrypted_chunk

                # Increment counter for next chunk
                counter += 1

        # Cache the file in the background
        self.cache_file_in_background(file_obj.id, decrypted_chunks)

    def decrypt_file_stream_from_drive(self, file_obj):
        """Generator to stream decrypt file data in chunks from Google Drive"""
        # Decode key and IV from base64
        key_bytes = base64.b64decode(file_obj.encryption_key)
        iv_bytes = base64.b64decode(file_obj.encryption_iv)

        # For CTR mode, we use a 12-byte nonce + 4-byte counter
        # Starting counter at 0
        counter = 0

        # Get file from Google Drive
        drive = GoogleDriveStorage()
        file_content = drive.download_file(file_obj.drive_file_id)

        # Create a list to store chunks for caching
        decrypted_chunks = []

        # Process file in chunks
        while True:
            chunk = file_content.read(self.CHUNK_SIZE)
            if not chunk:
                break

            # Decrypt the chunk
            decrypted_chunk = self.decrypt_chunk(chunk, key_bytes, iv_bytes, counter)

            # Store for caching
            decrypted_chunks.append(decrypted_chunk)

            # Yield the chunk for streaming
            yield decrypted_chunk

            # Increment counter for next chunk
            counter += 1

        # Cache the file in the background
        self.cache_file_in_background(file_obj.id, decrypted_chunks)

    def decrypt_file_stream(self, file_obj):
        """Generator to stream decrypt file data in chunks"""
        # Check if file is in cache
        if file_cache.file_exists(file_obj.id):
            # Return cached file content
            yield from file_cache.get_file_generator(file_obj.id, self.CHUNK_SIZE)
            return
            
        # If file is still being uploaded to Google Drive, try to serve from local storage
        if file_obj.upload_status == "pending" and file_obj.local_path:
            try:
                yield from self.decrypt_file_stream_from_local(file_obj)
                return
            except FileNotFoundError:
                # If local file is not found, fall back to Google Drive if available
                if not file_obj.drive_file_id:
                    raise Http404("File content not found locally or in Google Drive")
        
        # If file is in Google Drive, serve from there
        if file_obj.drive_file_id:
            yield from self.decrypt_file_stream_from_drive(file_obj)
            return
            
        # If we get here, we couldn't find the file content
        raise Http404("File content not found")

    def cache_file_in_background(self, file_id, chunks):
        """Cache the file in the background"""

        def cache_task():
            try:
                file_cache.save_file(file_id, chunks)
            except Exception as e:
                print(f"Error caching file {file_id}: {e}")

        thread = threading.Thread(target=cache_task)
        thread.daemon = True
        thread.start()

    def get(self, request, pk, format=None):
        """Handle GET request for file download with streaming"""
        try:
            # Get the file by UUID
            file_obj = CloudFile.objects.get(id=pk, owner=request.user)
        except CloudFile.DoesNotExist:
            raise Http404("File not found")

        # Check if file content is available (either in Google Drive or local storage)
        if not file_obj.drive_file_id and (file_obj.upload_status != "pending" or not file_obj.local_path):
            raise Http404("File content not found")

        # Create streaming response with decrypted data
        response = StreamingHttpResponse(
            self.decrypt_file_stream(file_obj), content_type=file_obj.mime_type or "application/octet-stream"
        )

        # Set content disposition to attachment with the original filename
        response["Content-Disposition"] = f'attachment; filename="{file_obj.name}"'

        # Set Content-Length if known
        if file_obj.size:
            response["Content-Length"] = file_obj.size

        return response


class FileUploadView(APIView):
    """View for handling multiple file uploads with encryption"""

    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]
    # Buffer size: 10MB chunks for processing
    CHUNK_SIZE = 10 * 1024 * 1024
    # Local uploads directory
    UPLOADS_DIR = Path(settings.MEDIA_ROOT) / "file_uploads"

    def encrypt_large_file(self, uploaded_file):
        """Process large file encryption in chunks using AES-256 CTR mode"""
        # Generate a secure random 256-bit (32-byte) key for AES-256
        key = secrets.token_bytes(32)
        # Generate a secure random 96-bit (12-byte) nonce for CTR mode
        # (Counter will be the remaining 4 bytes, starting at 0)
        iv = secrets.token_bytes(12)

        # Create a file UUID for storage
        file_uuid = str(uuid.uuid4())
        
        # Create directory for this file
        file_dir = self.UPLOADS_DIR / file_uuid
        file_dir.mkdir(exist_ok=True, parents=True)
        
        # Create file path for encrypted content
        encrypted_file_path = file_dir / uploaded_file.name

        # Track file size
        file_size = 0
        counter = 0

        try:
            # Process the file in chunks
            with open(encrypted_file_path, 'wb') as encrypted_file:
                for chunk in uploaded_file.chunks(self.CHUNK_SIZE):
                    # Update file size
                    file_size += len(chunk)

                    # Create CTR cipher for this chunk
                    cipher = Cipher(
                        algorithms.AES(key), modes.CTR(iv + counter.to_bytes(4, byteorder="big")), backend=default_backend()
                    )
                    encryptor = cipher.encryptor()

                    # Encrypt the chunk and write to file
                    encrypted_chunk = encryptor.update(chunk) + encryptor.finalize()
                    encrypted_file.write(encrypted_chunk)

                    # Increment counter for next chunk
                    counter += 1

            # Return the file path and encryption params
            return {
                "file_path": str(encrypted_file_path),
                "file_uuid": file_uuid,
                "size": file_size,
                "key": base64.b64encode(key).decode("utf-8"),
                "iv": base64.b64encode(iv).decode("utf-8"),
            }
        except Exception as e:
            # Clean up file in case of errors
            if encrypted_file_path.exists():
                encrypted_file_path.unlink()
            if file_dir.exists() and len(list(file_dir.iterdir())) == 0:
                file_dir.rmdir()
            raise e

    def create_or_get_directory(self, user, directory_name, parent=None):
        """Create a directory if it doesn't exist or get it if it does"""
        directory, created = Directory.objects.get_or_create(
            name=directory_name,
            owner=user,
            parent=parent,
        )
        return directory

    def create_directory_hierarchy(self, user, path_hierarchy):
        """Create or get a directory hierarchy from a list of directory names"""
        parent = None
        for directory_name in path_hierarchy:
            parent = self.create_or_get_directory(user, directory_name, parent)
        return parent

    @staticmethod
    def upload_to_drive_in_background(file_id, temp_file_path, file_name):
        """Upload encrypted file to Google Drive in the background"""
        try:
            drive = GoogleDriveStorage()
            drive_file = drive.upload_file(
                file_path=temp_file_path, file_name=file_name, mime_type="application/octet-stream", file_id=str(file_id)
            )

            # Update file with Drive ID in a separate transaction
            with transaction.atomic():
                file_obj = CloudFile.objects.get(id=file_id)
                file_obj.drive_file_id = drive_file["id"]
                file_obj.upload_status = "completed"
                # We no longer need to store the local path after successful upload
                file_obj.local_path = None
                file_obj.save()

            # Delete the local file after successful upload
            if os.path.exists(temp_file_path):
                try:
                    # Get the UUID folder path (parent directory of the file)
                    uuid_folder = os.path.dirname(temp_file_path)
                    
                    # Delete the file first
                    os.remove(temp_file_path)
                    
                    # Check if the UUID folder is empty
                    if os.path.exists(uuid_folder) and len(os.listdir(uuid_folder)) == 0:
                        # If empty, remove the UUID folder
                        os.rmdir(uuid_folder)
                except Exception as e:
                    print(f"Error deleting local file after upload: {str(e)}")

        except Exception as e:
            # Handle errors - update file status to reflect failure
            try:
                with transaction.atomic():
                    file_obj = CloudFile.objects.get(id=file_id)
                    file_obj.upload_status = "failed"
                    file_obj.local_path = temp_file_path  # Keep local path on failure
                    file_obj.save()
            except Exception as inner_e:
                print(f"Error updating file status: {inner_e}")

            # Log the error
            print(f"Error uploading file to Google Drive: {str(e)}")

    def post(self, request, format=None):
        """Handle POST request for multiple file uploads"""
        parent_dir_id = request.data.get("parent_directory") or request.data.get("parent")
        parent_directory = None
        # Parse auto_organize from request, default to True if not specified or from upload page
        use_auto_organization = str(request.data.get("auto_organize", "true")).lower() == "true"

        # Check if a parent directory was specified and it exists
        if parent_dir_id:
            try:
                parent_directory = Directory.objects.get(id=parent_dir_id, owner=request.user)
            except Directory.DoesNotExist:
                return Response({"error": "Parent directory not found"}, status=status.HTTP_404_NOT_FOUND)

        files = request.FILES.getlist("files")
        if not files:
            return Response({"error": "No files provided"}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_files = []

        for uploaded_file in files:
            try:
                # Determine file category based on filename
                main_category, sub_category = check_type(uploaded_file.name)
                category = main_category

                # Extract creation date from filename
                file_date = extract_date_from_filename(uploaded_file.name)

                # Determine parent directory based on auto-organization
                file_parent = parent_directory
                if use_auto_organization:
                    # Get directory path hierarchy from filename
                    path_hierarchy = get_directory_path(uploaded_file.name)
                    if path_hierarchy:
                        # Create directory hierarchy and use the leaf directory as parent
                        with transaction.atomic():
                            file_parent = self.create_directory_hierarchy(request.user, path_hierarchy)

                # Handle large file encryption (non-database operation)
                encryption_result = self.encrypt_large_file(uploaded_file)

                # Create file record in database
                with transaction.atomic():
                    file_obj = CloudFile(
                        name=uploaded_file.name,
                        owner=request.user,
                        parent=file_parent,
                        size=encryption_result["size"],
                        mime_type=uploaded_file.content_type or "application/octet-stream",
                        encryption_key=encryption_result["key"],
                        encryption_iv=encryption_result["iv"],
                        category=category,
                        created_at=file_date,
                        upload_status="pending",  # Mark as pending until Google Drive upload completes
                        local_path=encryption_result["file_path"]  # Store path to local encrypted file
                    )

                    # Save the file object to get an ID
                    file_obj.save()

                # Start Google Drive upload in background thread
                temp_file_path = encryption_result["file_path"]
                thread = threading.Thread(
                    target=self.upload_to_drive_in_background, args=(file_obj.id, temp_file_path, uploaded_file.name)
                )
                thread.daemon = True  # Allow the thread to be terminated when main thread exits
                thread.start()

                # Add the file to response immediately
                uploaded_files.append(FileSerializer(file_obj, context={"request": request}).data)

            except Exception as e:
                # Log the error
                print(f"Error processing file {uploaded_file.name}: {str(e)}")
                # Continue with the next file instead of failing the entire request
                continue

        return Response({"files": uploaded_files}, status=status.HTTP_201_CREATED)


class GalleryListView(APIView):
    """View for listing media files (images and videos) for the authenticated user"""

    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        """Get all media files (with category Pictures or Videos) owned by the authenticated user"""
        # Get optional query parameters
        parent_id = request.query_params.get("parent", None)

        # Define media categories to include in gallery
        media_categories = ["Pictures", "Videos"]

        from django.db.models import Q

        # Build query to match any media category - case insensitive
        category_query = Q(category__iexact=media_categories[0])
        for category in media_categories[1:]:
            category_query |= Q(category__iexact=category)

        # Start building the queryset - filter by owner and categories
        queryset = CloudFile.objects.filter(category_query, owner=request.user)

        # If no results found, try a more flexible query that checks if category contains these words
        if queryset.count() == 0:
            category_query = (
                Q(category__icontains="picture") | Q(category__icontains="video") | Q(category__icontains="image")
            )
            queryset = CloudFile.objects.filter(category_query, owner=request.user)

        # Filter by parent directory if specified
        if parent_id:
            try:
                parent = Directory.objects.get(id=parent_id, owner=request.user)
                queryset = queryset.filter(parent=parent)
            except Directory.DoesNotExist:
                return Response({"error": "Parent directory not found"}, status=status.HTTP_404_NOT_FOUND)
        # Remove the else clause that was filtering to only root files
        # This way we return ALL media files when no parent is specified

        # If still no results found, return a more descriptive response
        if queryset.count() == 0:
            # Check if there are any files for this user at all
            total_files = CloudFile.objects.filter(owner=request.user).count()
            if total_files > 0:
                # Get a list of unique categories for debugging
                categories = CloudFile.objects.filter(owner=request.user).values_list("category", flat=True).distinct()
                return Response(
                    {
                        "message": "No media files found with the categories Pictures or Videos.",
                        "debug_info": {"total_files": total_files, "available_categories": list(categories)},
                    }
                )

        serializer = FileSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)


class ExplorerView(APIView):
    """View for listing both directories and files together with breadcrumbs"""

    permission_classes = [IsAuthenticated]

    def get_breadcrumbs(self, directory):
        """
        Generate a breadcrumb trail for navigation
        Returns a list of directories from root to the current directory
        """
        breadcrumbs = []
        current = directory

        # Traverse up the directory tree to build breadcrumbs
        while current:
            breadcrumbs.insert(0, current)
            current = current.parent

        return breadcrumbs

    def get(self, request, format=None):
        """Get both directories and files with optional parent filter"""
        # Get optional query parameter
        parent_id = request.query_params.get("parent", None)

        # Initialize breadcrumbs as an empty list (for root directory)
        breadcrumbs = []
        current_directory = None

        # Filter by parent directory if specified
        if parent_id:
            try:
                current_directory = Directory.objects.get(id=parent_id, owner=request.user)
                directories = Directory.objects.filter(owner=request.user, parent=current_directory)
                files = CloudFile.objects.filter(owner=request.user, parent=current_directory)

                # Generate breadcrumbs for the current directory
                breadcrumbs = self.get_breadcrumbs(current_directory)
            except Directory.DoesNotExist:
                return Response({"error": "Parent directory not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Get directories and files in root directory (parent=None)
            directories = Directory.objects.filter(owner=request.user, parent=None)
            files = CloudFile.objects.filter(owner=request.user, parent=None)

        # Serialize the data
        directory_serializer = DirectorySerializer(directories, many=True)
        file_serializer = FileSerializer(files, many=True, context={"request": request})
        breadcrumb_serializer = BreadcrumbSerializer(breadcrumbs, many=True)

        # Return combined response
        return Response(
            {
                "directories": directory_serializer.data,
                "files": file_serializer.data,
                "breadcrumbs": breadcrumb_serializer.data,
                "current_directory": BreadcrumbSerializer(current_directory).data if current_directory else None,
            }
        )

    def post(self, request, format=None):
        """Create a new directory"""
        serializer = DirectorySerializer(data=request.data)
        if serializer.is_valid():
            # Ensure that the owner is the authenticated user
            serializer.validated_data["owner"] = request.user

            # If parent is specified, ensure it exists and belongs to the user
            parent_id = serializer.validated_data.get("parent", None)
            if parent_id:
                try:
                    parent = Directory.objects.get(id=parent_id, owner=request.user)
                    serializer.validated_data["parent"] = parent
                except Directory.DoesNotExist:
                    return Response({"error": "Parent directory not found"}, status=status.HTTP_404_NOT_FOUND)

            # Save the directory
            directory = serializer.save()
            return Response(DirectorySerializer(directory).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for managing file tags"""
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only tags owned by the current user"""
        return Tag.objects.filter(owner=self.request.user)
        
    def create(self, request, *args, **kwargs):
        """Create a new tag with validation for file ownership"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Only accept file_ids as an array
        file_ids = request.data.get('file_ids')
        
        # Check if file_ids is provided and is an array
        if not file_ids:
            return Response(
                {"error": "file_ids is required and must be an array"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Verify file_ids is actually an array
        if not isinstance(file_ids, list):
            return Response(
                {"error": "file_ids must be an array, even for a single file"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate that all files exist and belong to the current user
        files = []
        for fid in file_ids:
            try:
                file = CloudFile.objects.get(id=fid, owner=request.user)
                files.append(file)
            except CloudFile.DoesNotExist:
                return Response(
                    {"error": f"File with id {fid} not found or you don't have permission to tag this file"},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Create the tag
        tag = serializer.save(owner=request.user)
        
        # Create FileTag associations for all files
        for file in files:
            FileTag.objects.create(file=file, tag=tag)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_update(self, serializer):
        """Update an existing tag"""
        serializer.save()

    def perform_destroy(self, instance):
        """Delete a tag"""
        instance.delete()

    @action(detail=True, methods=['get'])
    def files(self, request, pk=None):
        """Get all files associated with a tag"""
        tag = self.get_object()  # This will use get_queryset, ensuring the user owns the tag
        
        # Get all FileTag entries for this tag
        file_tags = FileTag.objects.filter(tag=tag)
        files = [ft.file for ft in file_tags]
        
        # Serialize the files
        serializer = FileSerializer(files, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def tag_files(self, request, pk=None):
        """Add files to an existing tag"""
        tag = self.get_object()
        
        # Get file IDs from request
        file_ids = request.data.get('file_ids')
        if not file_ids:
            return Response(
                {"error": "file_ids is required and must be an array"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Verify file_ids is actually an array
        if not isinstance(file_ids, list):
            return Response(
                {"error": "file_ids must be an array, even for a single file"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate files exist and belong to user
        added_files = []
        errors = []
        
        for file_id in file_ids:
            try:
                file = CloudFile.objects.get(id=file_id, owner=request.user)
                
                # Check if this file is already tagged
                file_tag, created = FileTag.objects.get_or_create(file=file, tag=tag)
                
                if created:
                    added_files.append(FileSerializer(file, context={'request': request}).data)
                else:
                    errors.append(f"File {file_id} is already tagged with this tag")
                    
            except CloudFile.DoesNotExist:
                errors.append(f"File {file_id} not found or you don't have permission to tag it")
        
        return Response({
            "tag": TagSerializer(tag).data,
            "added_files": added_files,
            "errors": errors
        })
    
    @action(detail=True, methods=['post'])
    def untag_files(self, request, pk=None):
        """Remove files from a tag"""
        tag = self.get_object()
        
        # Get file IDs from request
        file_ids = request.data.get('file_ids')
        if not file_ids:
            return Response(
                {"error": "file_ids is required and must be an array"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Verify file_ids is actually an array
        if not isinstance(file_ids, list):
            return Response(
                {"error": "file_ids must be an array, even for a single file"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process file removals
        removed_files = []
        errors = []
        
        for file_id in file_ids:
            try:
                file = CloudFile.objects.get(id=file_id, owner=request.user)
                
                try:
                    # Find and delete the FileTag association
                    file_tag = FileTag.objects.get(file=file, tag=tag)
                    file_tag.delete()
                    removed_files.append(FileSerializer(file, context={'request': request}).data)
                except FileTag.DoesNotExist:
                    errors.append(f"File {file_id} was not tagged with this tag")
                    
            except CloudFile.DoesNotExist:
                errors.append(f"File {file_id} not found or you don't have permission to modify its tags")
        
        return Response({
            "tag": TagSerializer(tag).data,
            "removed_files": removed_files,
            "errors": errors
        })
