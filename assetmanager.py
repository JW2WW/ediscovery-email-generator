import os
import io
import zipfile
import random
import time
from email.mime.base import MIMEBase
from email import encoders
from email.policy import SMTP

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")

OFFICE_EXTENSIONS = {".pdf", ".xls", ".xlsx", ".doc", ".docx", ".ppt", ".pptx"}

MIME_TYPES = {
    ".pdf": ("application", "pdf"),
    ".xls": ("application", "vnd.ms-excel"),
    ".xlsx": ("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ".doc": ("application", "msword"),
    ".docx": ("application", "vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ".ppt": ("application", "vnd.ms-powerpoint"),
    ".pptx": ("application", "vnd.openxmlformats-officedocument.presentationml.presentation"),
    ".zip": ("application", "zip"),
    ".eml": ("application", "octet-stream"),
    ".json": ("application", "json"),
    ".xml": ("application", "xml"),
    ".txt": ("text", "plain"),
}


def _list_sample_files(extensions=None):
    if not os.path.exists(SAMPLES_DIR):
        return []
    files = []
    for name in os.listdir(SAMPLES_DIR):
        path = os.path.join(SAMPLES_DIR, name)
        if not os.path.isfile(path):
            continue
        if extensions is None:
            files.append(path)
        else:
            ext = os.path.splitext(name)[1].lower()
            if ext in extensions:
                files.append(path)
    return files


def get_random_local_attachment(extensions=None):
    """Return a random file from the samples pool, optionally filtered by extension."""
    files = _list_sample_files(extensions)
    return random.choice(files) if files else None


def get_random_office_attachment():
    """Return a random office-format file (pdf, xls, xlsx, doc, docx, ppt, pptx)."""
    return get_random_local_attachment(OFFICE_EXTENSIONS)


def create_mime_attachment(filepath):
    """Build a properly-typed MIME attachment part from a local file."""
    ext = os.path.splitext(filepath)[1].lower()
    maintype, subtype = MIME_TYPES.get(ext, ("application", "octet-stream"))
    part = MIMEBase(maintype, subtype, policy=SMTP)
    with open(filepath, "rb") as f:
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment", filename=os.path.basename(filepath))
    return part


def create_nested_eml_attachment(child_msg):
    inner_buffer = io.BytesIO()
    from email.generator import BytesGenerator
    inner_gen = BytesGenerator(inner_buffer, policy=SMTP)
    inner_gen.flatten(child_msg)
    safe_eml_bytes = inner_buffer.getvalue()

    attachment_part = MIMEBase("application", "octet-stream", policy=SMTP)
    attachment_part.set_payload(safe_eml_bytes)
    encoders.encode_base64(attachment_part)

    eml_filename = f"FW_{time.strftime('%Y%m%d')}_{random.randint(100, 999)}.eml"
    attachment_part.add_header("Content-Disposition", "attachment", filename=eml_filename)
    return attachment_part


def create_complex_zip_attachment(dynamic_eml, msg_subject, msg_body, extra_files=None):
    """ZIP archive with an inner .eml, a notice, and optional office documents."""
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        inner_buffer = io.BytesIO()
        from email.generator import BytesGenerator
        inner_gen = BytesGenerator(inner_buffer, policy=SMTP)
        inner_gen.flatten(dynamic_eml)
        zip_file.writestr("correspondence_thread.eml", inner_buffer.getvalue())

        notice_content = (
            f"INTERNAL DISTRIBUTION\n"
            f"====================\n"
            f"Subject: {msg_subject}\n"
            f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"{msg_body}\n"
        )
        zip_file.writestr("readme.txt", notice_content.encode("utf-8"))

        if extra_files:
            for fpath in extra_files:
                if fpath and os.path.isfile(fpath):
                    zip_file.write(fpath, os.path.basename(fpath))

    zip_buffer.seek(0)
    attachment_part = MIMEBase("application", "zip", policy=SMTP)
    attachment_part.set_payload(zip_buffer.getvalue())
    encoders.encode_base64(attachment_part)

    zip_filename = f"attachments_{time.strftime('%Y%m%d')}_{random.randint(100, 999)}.zip"
    attachment_part.add_header("Content-Disposition", "attachment", filename=zip_filename)
    return attachment_part
