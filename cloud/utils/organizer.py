import os
from datetime import datetime, timezone

# Define the destination directory
DESTINATION_DIR = "exports"


def any_in(checks, target):
    for check in checks:
        if check in target:
            return True
    return False


def check_type(raw_name, other=False):
    """
    Determine the file type category based on the filename.

    Returns a tuple of (main_category, sub_category) to build the folder structure.
    """
    raw_name_lower = raw_name.lower()

    # Audio files
    if raw_name.endswith((".opus", ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac")):
        return ("Audio", "Voice Notes" if raw_name.endswith(".opus") else None)
    if any_in([")_", "call"], raw_name_lower):
        return ("Audio", "Call Records")

    # Video files
    if raw_name.endswith((".mp4", ".MP4", ".mov", ".MOV", ".avi", ".AVI", ".mkv", ".webm", ".flv", ".3gp")):
        return ("Videos", None)
    if "record" in raw_name_lower or "screenrecord" in raw_name_lower:
        return ("Videos", "Screen Records")

    # Image files
    if raw_name.endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic", ".JPG", ".JPEG", ".PNG")):
        return ("Pictures", None)
    # Updated screenshot detection to handle "Screenshot_" pattern
    if raw_name.startswith(("Screenshot", "Screenshot_")):
        return ("Pictures", "Screenshots")
    if raw_name.startswith(("IMG_", "IMG-", "MVIMG_")) and not raw_name.endswith((".mp4", ".MP4", ".mov", ".MOV")):
        return ("Pictures", None)

    # Document files
    if raw_name.startswith("DOC") or raw_name.endswith(
        (
            ".pdf",
            ".csv",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".txt",
            ".rtf",
            ".odt",
            ".ods",
            ".odp",
            ".htm",
            ".html",
            ".xml",
            ".json",
        )
    ):
        return ("Documents", None)

    # Archives
    if raw_name.endswith((".zip", ".rar", ".7z", ".tar", ".gz", ".bz2")):
        return ("Archives", None)

    # Applications/Executables
    if raw_name.endswith((".apk", ".exe", ".msi", ".dmg", ".app", ".sh", ".bat")):
        return ("Applications", None)

    # Default: Return "Other" only when truly unknown
    return ("Other", None)


def get_directory_path(filename):
    """
    Get the destination directory path for a file based on its timestamp.
    Returns a list of directory names that form the path hierarchy.

    Args:
        filename (str): The name of the file to process

    Returns:
        list: A list of directory names forming the hierarchy, or None if path cannot be determined
    """
    timestamp1 = ("IMG_", "VID_", "MVIMG_", "SAVE_", "MVIMG_")
    timestamp2 = ("IMG-", "AUD-", "PTT-", "VID-", "null-", "DOC")
    timestamp3 = ("2017-", "2018-", "2019-", "2020-", "2021-", "2022-", "2023-", "2024-")
    timestamp4 = ("2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024")
    timestamp5 = ("Screenshot_",)
    timestamp6 = ("Screenrecorder-",)
    timestamp7 = ("IMG20",)
    timestamp8 = (")_", "call_")
    timestamp9 = ("WhatsApp ", "Screen Recording")
    timestamp10 = ("Screenshot ",)
    timestamp11 = ("VID",)

    # Skip hidden files
    if filename.startswith("."):
        return None

    # Skip text files (chat files) as requested
    if filename.endswith(".txt"):
        return None

    try:
        is_other = False
        try:
            is_raw = bool(datetime.fromtimestamp(float(filename.split(".")[0]), timezone.utc))
        except:
            is_raw = False

        if (
            not filename.startswith(
                timestamp1
                + timestamp2
                + timestamp3
                + timestamp4
                + timestamp5
                + timestamp6
                + timestamp7
                + timestamp9
                + timestamp10
                + timestamp11
            )
            and not any_in(timestamp8, filename)
        ) and not is_raw:
            is_other = True
            timestamp = str(datetime.today().strftime(r"%Y%m%d"))
        elif filename.startswith(timestamp1):
            timestamp = filename.split("_")[1]
        elif filename.startswith(timestamp2):
            timestamp = filename.split("-")[1]
        elif filename.startswith(timestamp3):
            pre = str(filename.split(".")[0]).split("-")
            timestamp = f"{pre[0]}{pre[1]}{pre[2]}"
        elif filename.startswith(timestamp4):
            timestamp = filename.split("_")[0]
        elif filename.startswith(timestamp5):
            if "com." in filename:
                pre = str(filename.split("_")[1]).split("-")
                timestamp = f"{pre[0]}{pre[1]}{pre[2]}"
            else:
                timestamp = str(filename.split("_")[1]).split("-", maxsplit=1)[0]
        elif filename.startswith(timestamp6):
            pre = filename.split("-")
            timestamp = f"{pre[1]}{pre[2]}{pre[3]}"
        elif filename.startswith(timestamp7):
            timestamp = filename.split(".")[0][3:11]
        elif any_in(timestamp8, filename):
            timestamp = f"{filename.split('_')[1].split('.')[0]}"[:8]
        elif filename.startswith(timestamp9):
            timestamp = f"{filename.split(' ')[2].replace('-', '')}"
        elif filename.startswith(timestamp10):
            timestamp = f"{filename.split(' ')[1].replace('-', '')}"
        elif filename.startswith(timestamp11):
            timestamp = f"{filename[3:11]}"
        elif is_raw:
            timestamp = datetime.fromtimestamp(float(filename.split(".")[0]), timezone.utc).strftime("%Y%m%d")
        else:
            return None

        try:
            date = datetime.strptime(timestamp, "%Y%m%d")
        except:
            timestamp = str(datetime.today().strftime(r"%Y%m%d"))
            date = datetime.strptime(timestamp, "%Y%m%d")

        # Get file type and create the folder hierarchy
        main_category, sub_category = check_type(filename, is_other)

        # Create path hierarchy with main category always first
        path_hierarchy = [main_category]

        # Add subcategory if it exists
        if sub_category:
            path_hierarchy.append(sub_category)

        # Force screenshot pattern detection regardless of timestamp extraction
        # This ensures all screenshot files go to Screenshots subfolder
        if filename.startswith(("Screenshot", "Screenshot_")):
            if len(path_hierarchy) == 1:  # Only has main category
                path_hierarchy.append("Screenshots")
            elif path_hierarchy[1] != "Screenshots":  # Has wrong subcategory
                path_hierarchy[1] = "Screenshots"

        # Debug output
        print(f"Final path hierarchy for {filename}: {path_hierarchy}")

        return path_hierarchy

    except:
        # If anything fails, just use the file type categorization
        main_category, sub_category = check_type(filename, True)
        path_hierarchy = [main_category]
        if sub_category:
            path_hierarchy.append(sub_category)
            # Add debug print
            print(f"Exception handler - File: {filename}, Category: {main_category}, Subcategory: {sub_category}")
        return path_hierarchy


def get_file_destination(filename, destination_dir=DESTINATION_DIR):
    """
    Get the destination filepath for a file based on its timestamp.

    Args:
        filename (str): The name of the file to process
        destination_dir (str): The base destination directory

    Returns:
        str: The destination filepath, or None if the filepath cannot be determined
    """
    path_hierarchy = get_directory_path(filename)
    if not path_hierarchy:
        return None

    # Build the full path
    current_path = destination_dir
    for folder in path_hierarchy:
        current_path = os.path.join(current_path, folder)

    return os.path.join(current_path, filename)


def extract_date_from_filename(filename):
    """
    Extract the date from a filename using the same logic as get_directory_path.

    Args:
        filename (str): The name of the file to process

    Returns:
        datetime: The extracted date, or today's date if extraction fails
    """
    timestamp1 = ("IMG_", "VID_", "MVIMG_", "SAVE_", "MVIMG_")
    timestamp2 = ("IMG-", "AUD-", "PTT-", "VID-", "null-", "DOC")
    timestamp3 = ("2017-", "2018-", "2019-", "2020-", "2021-", "2022-", "2023-", "2024-")
    timestamp4 = ("2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024")
    timestamp5 = ("Screenshot_",)
    timestamp6 = ("Screenrecorder-",)
    timestamp7 = ("IMG20",)
    timestamp8 = (")_", "call_")
    timestamp9 = ("WhatsApp ", "Screen Recording")
    timestamp10 = ("Screenshot ",)
    timestamp11 = ("VID",)

    try:
        try:
            is_raw = bool(datetime.fromtimestamp(float(filename.split(".")[0]), timezone.utc))
        except:
            is_raw = False

        if (
            not filename.startswith(
                timestamp1
                + timestamp2
                + timestamp3
                + timestamp4
                + timestamp5
                + timestamp6
                + timestamp7
                + timestamp9
                + timestamp10
                + timestamp11
            )
            and not any_in(timestamp8, filename)
        ) and not is_raw:
            timestamp = str(datetime.today().strftime(r"%Y%m%d"))
        elif filename.startswith(timestamp1):
            timestamp = filename.split("_")[1]
        elif filename.startswith(timestamp2):
            timestamp = filename.split("-")[1]
        elif filename.startswith(timestamp3):
            pre = str(filename.split(".")[0]).split("-")
            timestamp = f"{pre[0]}{pre[1]}{pre[2]}"
        elif filename.startswith(timestamp4):
            timestamp = filename.split("_")[0]
        elif filename.startswith(timestamp5):
            if "com." in filename:
                pre = str(filename.split("_")[1]).split("-")
                timestamp = f"{pre[0]}{pre[1]}{pre[2]}"
            else:
                timestamp = str(filename.split("_")[1]).split("-", maxsplit=1)[0]
        elif filename.startswith(timestamp6):
            pre = filename.split("-")
            timestamp = f"{pre[1]}{pre[2]}{pre[3]}"
        elif filename.startswith(timestamp7):
            timestamp = filename.split(".")[0][3:11]
        elif any_in(timestamp8, filename):
            timestamp = f"{filename.split('_')[1].split('.')[0]}"[:8]
        elif filename.startswith(timestamp9):
            timestamp = f"{filename.split(' ')[2].replace('-', '')}"
        elif filename.startswith(timestamp10):
            timestamp = f"{filename.split(' ')[1].replace('-', '')}"
        elif filename.startswith(timestamp11):
            timestamp = f"{filename[3:11]}"
        elif is_raw:
            timestamp = datetime.fromtimestamp(float(filename.split(".")[0]), timezone.utc).strftime("%Y%m%d")
        else:
            return datetime.today()

        try:
            date = datetime.strptime(timestamp, "%Y%m%d")
            return date
        except:
            return datetime.today()

    except:
        return datetime.today()
