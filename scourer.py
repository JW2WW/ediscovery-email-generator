import os
import urllib.request
import random

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
USER_AGENT = "Mozilla/5.0 (compatible; eDiscoveryComplianceMatrix/2.0)"


def harvest_federal_register():
    year = random.choice(["2024", "2025"])
    month, day = f"{random.randint(1, 12):02d}", f"{random.randint(1, 28):02d}"
    url = f"https://www.federalregister.gov/data/documents/{year}/{month}/{day}/bulk_xml.xml"
    filename = f"fed_reg_{year}_{month}_{day}.xml"
    return url, filename, 1500


def harvest_congressional_bills():
    year = random.choice(["2024", "2025"])
    bill_id = random.randint(1, 500)
    url = f"https://www.govinfo.gov/bulkdata/json/BILLS/{year}/1/hr/BILLS-{year}hr{bill_id}ih.json"
    filename = f"congress_bill_{year}_hr{bill_id}.json"
    return url, filename, 1500


def harvest_govinfo_pdf():
    """Download a real congressional bill PDF from GovInfo."""
    congress = random.choice([118, 119])
    bill_id = random.randint(1, 200)
    versions = ["ih", "rh", "eh", "enr"]
    version = random.choice(versions)
    package_id = f"BILLS-{congress}hr{bill_id}{version}"
    url = f"https://www.govinfo.gov/content/pkg/{package_id}/pdf/{package_id}.pdf"
    filename = f"HR{bill_id}_{congress}th_Congress.pdf"
    return url, filename, 5000


def harvest_federal_register_pdf():
    """Download a Federal Register issue PDF."""
    year = random.choice([2024, 2025])
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    fr_date = f"{year}-{month:02d}-{day:02d}"
    url = f"https://www.govinfo.gov/content/pkg/FR-{fr_date}/pdf/FR-{fr_date}.pdf"
    filename = f"Federal_Register_{year}_{month:02d}_{day:02d}.pdf"
    return url, filename, 10000


import json
import xml.etree.ElementTree as ET

def _download_source(source_fn, retries=3):
    if not os.path.exists(SAMPLES_DIR):
        os.makedirs(SAMPLES_DIR)

    target_url, filename, min_size = source_fn()
    filepath = os.path.join(SAMPLES_DIR, filename)
    
    for attempt in range(retries):
        try:
            print(f"[*] Harvesting from: {source_fn.__name__} (Attempt {attempt + 1}/{retries})")
            print(f"[*] Endpoint: {target_url}")
            req = urllib.request.Request(target_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = response.read()

            if len(data) < min_size:
                print(f"[-] Downloaded data too small ({len(data)} bytes) for {filename}. Retrying...")
                continue
            
            # Specific content validation
            ext = os.path.splitext(filename)[1].lower()
            if ext == ".json":
                try:
                    json.loads(data)
                except json.JSONDecodeError:
                    print(f"[-] Invalid JSON content for {filename}. Retrying...")
                    continue
            elif ext == ".xml":
                try:
                    ET.fromstring(data)
                except ET.ParseError:
                    print(f"[-] Invalid XML content for {filename}. Retrying...")
                    continue

            with open(filepath, "wb") as output_file:
                output_file.write(data)
            print(f"[+] Harvested: {filename} ({len(data) // 1024} KB)")
            return True
        except Exception as e:
            print(f"[-] Harvest failed ({source_fn.__name__}, Attempt {attempt + 1}/{retries}): {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
            if attempt < retries - 1:
                time.sleep(1) # Wait a bit before retrying
    return False


def scour_web_for_attachments():
    """Try multiple sources; also seed locally-generated office documents."""
    sources = [
        harvest_govinfo_pdf,
        harvest_federal_register_pdf,
        harvest_federal_register,
        harvest_congressional_bills,
    ]
    random.shuffle(sources)

    harvested = False
    for source in sources:
        if _download_source(source):
            harvested = True
            break

    try:
        import docgenerator
        created = docgenerator.ensure_document_variety(count=3)
        if created:
            print(f"[+] Generated {len(created)} office documents locally")
            harvested = True
    except Exception as e:
        print(f"[-] Local document generation skipped: {e}")

    return harvested


if __name__ == "__main__":
    success = False
    attempts = 0
    while not success and attempts < 10:
        attempts += 1
        success = scour_web_for_attachments()
