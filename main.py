import time
import random
import configparser
import contentfetcher
import assetmanager
import mail_sender
import scourer
import docgenerator


def load_generation_settings():
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config.getint("generation", "batch_size", fallback=10)


def _attach_office_document(subject, body, ext=None):
    """Generate a fresh office doc tied to the email content and return a MIME part."""
    try:
        path = docgenerator.generate_random_document(subject, body, ext=ext)
        return assetmanager.create_mime_attachment(path)
    except Exception as e:
        print(f"[-] Document generation failed: {e}")
        return None


def _attach_from_pool(office_only=False):
    """Attach a file from the samples pool with correct MIME type."""
    if office_only:
        path = assetmanager.get_random_office_attachment()
    else:
        path = assetmanager.get_random_local_attachment()
    if path:
        return assetmanager.create_mime_attachment(path)
    return None


def run_test_pipeline():
    batch_size = load_generation_settings()
    print(f"[*] Starting eDiscovery data ingestion run. Goal: {batch_size} messages.")

    print("[*] Refreshing local asset pool before batch execution...")
    try:
        scourer.scour_web_for_attachments()
    except Exception as e:
        print(f"[-] Automated asset refresh skipped: {e}")

    success_count = 0

    for i in range(1, batch_size + 1):
        print(f"\n--- Processing Message [{i}/{batch_size}] ---")

        subject, body = contentfetcher.fetch_realistic_content()
        print(f"[+] Subject: '{subject}'")

        attachments = []
        dice_roll = random.random()

        if dice_roll < 0.35:
            print("[+] Attaching a generated office document.")
            part = _attach_office_document(subject, body)
            if part:
                attachments.append(part)

        elif dice_roll < 0.55:
            count = random.randint(2, 3)
            print(f"[+] Attaching {count} mixed office documents.")
            exts = docgenerator.OFFICE_EXTENSIONS.copy()
            random.shuffle(exts)
            for ext in exts[:count]:
                part = _attach_office_document(subject, body, ext=ext)
                if part:
                    attachments.append(part)

        elif dice_roll < 0.70:
            print("[+] Attaching a file from the samples pool.")
            part = _attach_from_pool(office_only=random.random() > 0.3)
            if part:
                attachments.append(part)

        elif dice_roll < 0.85:
            print("[+] Simulating a forwarded email thread (.eml).")
            inner_sub, inner_body = contentfetcher.fetch_realistic_content()
            inner_msg = mail_sender.build_custom_email(f"FW: {inner_sub}", inner_body)
            attachments.append(assetmanager.create_nested_eml_attachment(inner_msg))

        elif dice_roll < 0.95:
            print("[+] Building a ZIP archive with mixed enclosures.")
            inner_sub, inner_body = contentfetcher.fetch_realistic_content()
            inner_msg = mail_sender.build_custom_email(f"FW: {inner_sub}", inner_body)
            extra = []
            for ext in random.sample(docgenerator.OFFICE_EXTENSIONS, k=random.randint(1, 2)):
                try:
                    extra.append(docgenerator.generate_random_document(subject, body, ext=ext))
                except Exception:
                    pass
            zip_part = assetmanager.create_complex_zip_attachment(
                dynamic_eml=inner_msg,
                msg_subject=subject,
                msg_body=body,
                extra_files=extra,
            )
            attachments.append(zip_part)
        else:
            print("[+] Text-only email (no attachments).")

        master_msg = mail_sender.build_custom_email(subject, body, attachments=attachments)
        transmitted = mail_sender.transmit_email(master_msg)
        if transmitted:
            print("[+] Successfully delivered message to the SMTP engine.")
            success_count += 1
        else:
            print("[-] Ingestion block rejected or failed transmission.")

        time.sleep(0.2)

    print(f"\n[*] Execution Finished! Successfully sent {success_count}/{batch_size} messages.")


if __name__ == "__main__":
    run_test_pipeline()
