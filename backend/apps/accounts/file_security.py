import io
import os
import uuid
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError

Image.MAX_IMAGE_PIXELS = 25_000_000  # Decompression bomb defense: max 25M pixels
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

# Prohibited dangerous executable and script extensions
DANGEROUS_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.sh', '.bash', '.ps1', '.vbs', '.js',
    '.php', '.phtml', '.php3', '.php4', '.php5', '.phps', '.cgi', '.pl',
    '.py', '.pyc', '.pyo', '.jar', '.war', '.jsp', '.jspx', '.asp', '.aspx',
    '.html', '.htm', '.xhtml', '.shtml', '.svg', '.xml', '.dll', '.so', '.dylib'
}

# Magic signatures
MAGIC_SIGNATURES = {
    'jpeg': b'\xff\xd8\xff',
    'png': b'\x89PNG\r\n\x1a\n',
    'webp_riff': b'RIFF',
    'webp_tag': b'WEBP',
    'pdf': b'%PDF-'
}


def detect_file_type(raw_bytes: bytes) -> str:
    """Detects actual file signature from initial magic bytes."""
    if len(raw_bytes) < 12:
        return 'unknown'
    if raw_bytes[:3] == MAGIC_SIGNATURES['jpeg']:
        return 'jpeg'
    if raw_bytes[:8] == MAGIC_SIGNATURES['png']:
        return 'png'
    if raw_bytes[:4] == MAGIC_SIGNATURES['webp_riff'] and raw_bytes[8:12] == MAGIC_SIGNATURES['webp_tag']:
        return 'webp'
    if raw_bytes[:5] == MAGIC_SIGNATURES['pdf']:
        return 'pdf'
    return 'unknown'


def validate_and_sanitize_image(uploaded_file, max_size=MAX_FILE_SIZE_BYTES):
    """
    Validates file content, checks magic bytes, and decodes/re-encodes
    the image via Pillow to completely strip polyglot payloads, embedded scripts,
    and metadata. Returns a clean InMemoryUploadedFile.
    """
    if not uploaded_file:
        raise ValidationError('No image file provided.')

    if uploaded_file.size > max_size:
        max_mb = round(max_size / (1024 * 1024), 1)
        raise ValidationError(f'File size exceeds maximum allowed limit of {max_mb} MB.')

    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext in DANGEROUS_EXTENSIONS:
        raise ValidationError(f'Dangerous or executable file extension ({ext}) is strictly prohibited.')

    if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
        raise ValidationError(f'Unsupported image file extension ({ext}). Allowed formats are JPG, PNG, and WebP.')

    # Read binary content for signature check
    uploaded_file.seek(0)
    raw_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    detected_type = detect_file_type(raw_bytes)
    if detected_type not in ['jpeg', 'png', 'webp']:
        raise ValidationError('File content signature does not match a valid, safe image (JPEG/PNG/WebP).')

    # Decode and re-encode through Pillow to strip polyglot payloads and malicious headers
    try:
        in_buf = io.BytesIO(raw_bytes)
        img = Image.open(in_buf)
        img.verify()  # Header verification

        # Re-open for pixel decoding
        in_buf.seek(0)
        clean_img = Image.open(in_buf)

        # Decompression bomb and pixel dimensions protection
        if clean_img.width > 5000 or clean_img.height > 5000:
            raise ValidationError(f'Image resolution ({clean_img.width}x{clean_img.height}) exceeds maximum allowed 5000x5000 pixels.')

        # Convert palette or RGBA to RGB for JPEG compatibility
        target_format = 'JPEG' if detected_type == 'jpeg' else ('PNG' if detected_type == 'png' else 'WEBP')
        out_ext = '.jpg' if target_format == 'JPEG' else ('.png' if target_format == 'PNG' else '.webp')

        if target_format == 'JPEG' and clean_img.mode in ('RGBA', 'LA', 'P'):
            clean_img = clean_img.convert('RGB')

        out_buf = io.BytesIO()
        clean_img.save(out_buf, format=target_format, quality=85, optimize=True)
        out_buf.seek(0)
        sanitized_bytes = out_buf.getvalue()

        clean_filename = f"{uuid.uuid4().hex}{out_ext}"
        mime_type = f"image/{target_format.lower()}"

        sanitized_file = InMemoryUploadedFile(
            file=io.BytesIO(sanitized_bytes),
            field_name=uploaded_file.field_name if hasattr(uploaded_file, 'field_name') else 'file',
            name=clean_filename,
            content_type=mime_type,
            size=len(sanitized_bytes),
            charset=None
        )
        return sanitized_file

    except Exception as e:
        raise ValidationError(f'Corrupted or unreadable image file: {str(e)}')


def validate_and_sanitize_attachment(uploaded_file, max_size=MAX_FILE_SIZE_BYTES):
    """
    Validates general attachments (images or PDF documents).
    Images are re-encoded via Pillow; PDFs are validated against signature and script exploits.
    """
    if not uploaded_file:
        raise ValidationError('No file provided.')

    if uploaded_file.size > max_size:
        max_mb = round(max_size / (1024 * 1024), 1)
        raise ValidationError(f'File size exceeds maximum allowed limit of {max_mb} MB.')

    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext in DANGEROUS_EXTENSIONS:
        raise ValidationError(f'Dangerous or executable file extension ({ext}) is strictly prohibited.')

    uploaded_file.seek(0)
    raw_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    detected_type = detect_file_type(raw_bytes)

    # If it is an image, re-encode it
    if detected_type in ['jpeg', 'png', 'webp']:
        return validate_and_sanitize_image(uploaded_file, max_size)

    # If it is a PDF, verify header and inspect for active scripting
    if detected_type == 'pdf' and ext == '.pdf':
        lower_content = raw_bytes[:4096].lower()
        if b'/javascript' in lower_content or b'/launch' in lower_content:
            raise ValidationError('Malicious active script detected in uploaded PDF document.')
        
        clean_filename = f"{uuid.uuid4().hex}.pdf"
        sanitized_file = InMemoryUploadedFile(
            file=io.BytesIO(raw_bytes),
            field_name=uploaded_file.field_name if hasattr(uploaded_file, 'field_name') else 'file',
            name=clean_filename,
            content_type='application/pdf',
            size=len(raw_bytes),
            charset=None
        )
        return sanitized_file

    raise ValidationError(f'Invalid attachment format. Only verified PDF, JPG, PNG, and WebP files are permitted.')
