"""
Seed the database with sample RF component data.
Run: python seed.py (from the mrf_circuits directory)
"""
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))

from app.database import engine, SessionLocal, Base
from app.models.user import User
from app.models.product import Product, Category
from app.models.news import NewsArticle
from app.services.auth_service import AuthService
from datetime import date


def generate_mock_engineering_files(product_sku):
    import os
    import zipfile
    import math

    # Base paths
    static_dir = os.path.join(os.path.dirname(__file__), "app", "static")
    uploads_dir = os.path.join(static_dir, "uploads")

    ds_dir = os.path.join(uploads_dir, "datasheets")
    data_dir = os.path.join(uploads_dir, "data")
    pcb_dir = os.path.join(uploads_dir, "pcb")
    gerber_dir = os.path.join(uploads_dir, "gerber")

    for d in [ds_dir, data_dir, pcb_dir, gerber_dir]:
        os.makedirs(d, exist_ok=True)

    sku_lower = product_sku.lower()

    # 1. Datasheet PDF
    ds_path = os.path.join(ds_dir, f"{sku_lower}-datasheet.pdf")
    dummy_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF"
    with open(ds_path, "wb") as f:
        f.write(dummy_pdf)

    # 2. PCB Layout PDF
    pcb_path = os.path.join(pcb_dir, f"{sku_lower}-pcb.pdf")
    with open(pcb_path, "wb") as f:
        f.write(dummy_pdf)

    # 4. Calibration Data CSV
    data_path = os.path.join(data_dir, f"{sku_lower}-calibration.csv")

    # Generate CSV data points based on product type
    csv_lines = ["Frequency (GHz),Gain (dB),Noise Figure (dB),Return Loss (dB)"]

    # Determine frequency range
    if "2401" in product_sku or "2400" in product_sku:
        f_start, f_end = 2.3, 2.6
        g_center, nf_center, rl_center = 22.0, 0.5, -16.0
    elif "6001" in product_sku:
        f_start, f_end = 8.0, 12.0
        g_center, nf_center, rl_center = 25.0, 0.8, -15.0
    elif "5800" in product_sku:
        f_start, f_end = 5.6, 6.0
        g_center, nf_center, rl_center = -1.5, 0.0, -18.0
    elif "1575" in product_sku:
        f_start, f_end = 1.5, 1.6
        g_center, nf_center, rl_center = -1.2, 0.0, -20.0
    elif "3500" in product_sku:
        f_start, f_end = 3.3, 3.7
        g_center, nf_center, rl_center = 12.0, 3.5, -14.0
    else:
        f_start, f_end = 1.0, 10.0
        g_center, nf_center, rl_center = 15.0, 1.5, -12.0

    steps = 10
    for i in range(steps + 1):
        freq = f_start + (f_end - f_start) * (i / steps)
        # Add simple curves using quadratic/sine functions to look realistic
        norm_x = (i - steps/2) / (steps/2)  # -1 to 1
        gain = g_center - 1.5 * (norm_x ** 2) + 0.2 * math.sin(i)
        nf = nf_center + 0.3 * (norm_x ** 2) + 0.05 * math.cos(i) if nf_center > 0 else 0
        rl = rl_center - 3.0 * (1 - norm_x ** 2) + 0.5 * math.sin(i)

        csv_lines.append(f"{freq:.3f},{gain:.2f},{nf:.2f},{rl:.2f}")

    with open(data_path, "w") as f:
        f.write("\n".join(csv_lines))

    return {
        "datasheet_url": f"/static/uploads/datasheets/{sku_lower}-datasheet.pdf",
        "data_file_url": f"/static/uploads/data/{sku_lower}-calibration.csv",
        "pcb_layout_url": f"/static/uploads/pcb/{sku_lower}-pcb.pdf",
    }


def seed():
    # Create all tables
    # Import all models to ensure they are registered
    from app.models import address, cart, configurator, history, order, payment
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # --- Admin User ---
        if not db.query(User).filter(User.email == "admin@mrflab.com").first():
            admin = AuthService.create_user(
                db,
                username="admin",
                email="admin@mrflab.com",
                password="MRFAdmin2024!",
                full_name="MRF Admin",
                company="MRF Circuits",
            )
            admin.role = "admin"
            db.commit()
            print("[OK] Created admin user: admin@mrflab.com / MRFAdmin2024!")
        else:
            print("- Admin user already exists")

        # --- Test User ---
        if not db.query(User).filter(User.email == "engineer@test.com").first():
            AuthService.create_user(
                db,
                username="rf_engineer",
                email="engineer@test.com",
                password="test1234",
                full_name="Test Engineer",
                company="Test Corp",
            )
            print("[OK] Created test user: engineer@test.com / test1234")

        # --- Categories ---
        categories_data = [
            {"name": "Low Noise Amplifiers", "slug": "lna", "description": "Wideband and narrowband LNAs for receive chains"},
            {"name": "Band Pass Filters", "slug": "bpf", "description": "Microstrip and cavity band pass filters"},
            {"name": "VCOs & Oscillators", "slug": "vco", "description": "Voltage controlled and fixed oscillators"},
            {"name": "Power Dividers", "slug": "splitters", "description": "Wilkinson and resistive power dividers"},
            {"name": "Power Amplifiers", "slug": "pa", "description": "GaN and GaAs power amplifiers"},
            {"name": "Directional Couplers", "slug": "couplers", "description": "Hybrid and directional couplers"},
        ]
        cats = {}
        for cdata in categories_data:
            existing = db.query(Category).filter(Category.slug == cdata["slug"]).first()
            if not existing:
                cat = Category(**cdata)
                db.add(cat)
                db.flush()
                cats[cdata["slug"]] = cat
                print(f"[OK] Created category: {cdata['name']}")
            else:
                cats[cdata["slug"]] = existing
        db.commit()

        # --- Products ---
        products_data = [
            {
                "name": "MRF-LNA-2401 Low Noise Amplifier",
                "sku": "MRF-LNA-2401",
                "slug": "mrf-lna-2401",
                "description": "Ultra-low noise amplifier for 2.4 GHz ISM and WLAN applications. GaAs pHEMT technology with exceptional noise performance.",
                "price": 285.00,
                "stock_quantity": 24,
                "category_slug": "lna",
                "frequency_min": 2.3,
                "frequency_max": 2.6,
                "gain": 22.0,
                "noise_figure": 0.5,
            },
            {
                "name": "MRF-LNA-6001 X-Band LNA",
                "sku": "MRF-LNA-6001",
                "slug": "mrf-lna-6001",
                "description": "Wideband X-Band low noise amplifier for radar and satellite communications. 0.8 dB noise figure across full band.",
                "price": 420.00,
                "stock_quantity": 12,
                "category_slug": "lna",
                "frequency_min": 8.0,
                "frequency_max": 12.0,
                "gain": 25.0,
                "noise_figure": 0.8,
            },
            {
                "name": "MRF-BPF-5800 5.8GHz Filter",
                "sku": "MRF-BPF-5800",
                "slug": "mrf-bpf-5800",
                "description": "High-selectivity band pass filter for 5.8 GHz band. Microstrip construction on Rogers RO4003C substrate.",
                "price": 195.00,
                "stock_quantity": 30,
                "category_slug": "bpf",
                "frequency_min": 5.7,
                "frequency_max": 5.9,
            },
            {
                "name": "MRF-BPF-1575 GPS L1 Filter",
                "sku": "MRF-BPF-1575",
                "slug": "mrf-bpf-1575",
                "description": "Precision GPS L1 band pass filter at 1575.42 MHz. Minimal insertion loss for GPS receiver front-ends.",
                "price": 165.00,
                "stock_quantity": 45,
                "category_slug": "bpf",
                "frequency_min": 1.565,
                "frequency_max": 1.585,
            },
            {
                "name": "MRF-VCO-3500 S-Band VCO",
                "sku": "MRF-VCO-3500",
                "slug": "mrf-vco-3500",
                "description": "Low phase noise VCO covering 3.3-3.7 GHz. Ideal for 5G NR n78 band frequency synthesis.",
                "price": 340.00,
                "stock_quantity": 18,
                "category_slug": "vco",
                "frequency_min": 3.3,
                "frequency_max": 3.7,
            },
            {
                "name": "MRF-SPL-0212 2-Way Splitter",
                "sku": "MRF-SPL-0212",
                "slug": "mrf-spl-0212",
                "description": "Wideband 2-way Wilkinson power divider. Equal amplitude and phase splitting across 2-12 GHz.",
                "price": 125.00,
                "stock_quantity": 50,
                "category_slug": "splitters",
                "frequency_min": 2.0,
                "frequency_max": 12.0,
            },
            {
                "name": "MRF-PA-2400 2.4GHz Power Amplifier",
                "sku": "MRF-PA-2400",
                "slug": "mrf-pa-2400",
                "description": "GaN HEMT power amplifier for 2.4 GHz. 30 dBm output power with 45% PAE for wireless base stations.",
                "price": 680.00,
                "stock_quantity": 8,
                "category_slug": "pa",
                "frequency_min": 2.3,
                "frequency_max": 2.6,
                "gain": 28.0,
                "power_output": 30.0,
            },
            {
                "name": "MRF-CPL-3dB-DC18 Directional Coupler",
                "sku": "MRF-CPL-3DB-DC18",
                "slug": "mrf-cpl-3db-dc18",
                "description": "DC-18 GHz 3dB quadrature hybrid coupler. Ultra-wideband design for microwave test and measurement.",
                "price": 245.00,
                "stock_quantity": 20,
                "category_slug": "couplers",
                "frequency_min": 0.1,
                "frequency_max": 18.0,
            },
        ]

        for pdata in products_data:
            existing = db.query(Product).filter(Product.sku == pdata["sku"]).first()
            files_meta = generate_mock_engineering_files(pdata["sku"])
            if not existing:
                cat_slug = pdata.pop("category_slug")
                cat = cats.get(cat_slug)
                product = Product(
                    **pdata,
                    category_id=cat.id if cat else None,
                    is_active=True,
                    **files_meta
                )
                db.add(product)
                print(f"[OK] Created product: {product.name}")
            else:
                for k, v in files_meta.items():
                    setattr(existing, k, v)
                print(f"- Product already exists: {pdata['sku']} (updated engineering files)")
        db.commit()

        # --- News Articles ---
        news_data = [
            {
                "title": "MRF Circuits Achieves ISO 9001:2015 Certification",
                "excerpt": "Our quality management system now meets international standards, confirming our commitment to engineering excellence.",
                "content": "MRF Circuits is proud to announce the successful completion of ISO 9001:2015 certification. This milestone reflects our commitment to quality manufacturing processes and customer satisfaction.",
                "published_date": date(2024, 11, 15),
                "is_published": True,
            },
            {
                "title": "New GaN Power Amplifier Line Released",
                "excerpt": "Introducing the MRF-PA series: GaN HEMT amplifiers covering 0.5-6 GHz with industry-leading power efficiency.",
                "content": "The MRF-PA series leverages GaN-on-SiC technology to deliver exceptional power density and efficiency for base station and radar applications.",
                "published_date": date(2026, 10, 28),
                "is_published": True,
            },
            {
                "title": "Participation in EUMC 2026 — Paris",
                "excerpt": "MRF Circuits presented novel wideband filter designs at the European Microwave Conference, receiving industry recognition.",
                "content": "Our engineering team presented two technical papers on substrate-integrated waveguide (SIW) filter designs at EUMC 2026 in Paris.",
                "published_date": date(2026, 9, 20),
                "is_published": True,
            },
        ]

        for ndata in news_data:
            existing = db.query(NewsArticle).filter(NewsArticle.title == ndata["title"]).first()
            if not existing:
                article = NewsArticle(**ndata)
                db.add(article)
                print(f"[OK] Created news article: {ndata['title'][:40]}...")
        db.commit()

        print("\n[SUCCESS] Seed complete! Run the server with: uvicorn app.main:app --reload")
        print("Admin login: admin@mrflab.com / MRFAdmin2024!")
        print("Test login:  engineer@test.com / test1234")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
