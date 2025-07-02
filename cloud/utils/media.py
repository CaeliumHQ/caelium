import mimetypes
import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from cloud.models import MediaFile
from cloud.utils.organizer import check_type, extract_date_from_filename


def create_media(file, owner, category=None):
    """
    Create a MediaFile object and save the file to storage.

    Args:
        file: The uploaded file object
        owner: User object who owns the file
        category: Optional category override

    Returns:
        MediaFile: The created MediaFile instance
    """
    # Generate a unique ID for this media file
    media_id = uuid.uuid4()

    # Get the original filename
    filename = file.name

    # Extract date from filename using organizer
    extracted_date = extract_date_from_filename(filename)

    # Determine storage category (for path) if not provided
    storage_category = category
    if storage_category is None:
        main_category, _ = check_type(filename)
        storage_category = main_category.lower()

    # Determine file type for MediaFile model based on file content
    main_category, _ = check_type(filename)
    file_type_mapping = {
        "pictures": "image",
        "videos": "video",
        "audio": "audio",
        "documents": "document",
        "archives": "other",
        "applications": "other",
        "other": "other",
    }

    file_type = file_type_mapping.get(main_category.lower(), "other")

    # Get MIME type
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "application/octet-stream"

    # Get file size
    file_size = file.size

    # Create the storage path: media/{category}/{uuid}/filename.ext
    storage_path = f"media/{storage_category}/{media_id}/{filename}"

    # Save the file to storage
    saved_path = default_storage.save(storage_path, ContentFile(file.read()))

    # Create the MediaFile instance
    media_file = MediaFile.objects.create(
        id=media_id,
        filename=filename,
        location=saved_path,
        uploaded_by=owner,
        mime_type=mime_type,
        size=file_size,
        file_type=file_type,
        timestamp=extracted_date,
        storage_tier="hot",  # Default to hot storage
    )

    return media_file
