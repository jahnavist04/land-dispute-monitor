import click
from datetime import datetime, timedelta, timezone
from app import create_app
from app.extensions import db
from app.models.client import Client
from app.models.source import Source
from app.models.raw_article import RawArticle
from app.models.extracted_notice import ExtractedNotice
from app.models.dispute import Dispute
from app.models.subscription import Subscription
from app.models.alert import Alert

app = create_app()

@app.cli.command("init-db")
def init_db():
    """Initialize the database."""
    with app.app_context():
        db.create_all()
        click.echo('Database initialized.')

@app.cli.command("seed-sources")
def seed_sources():
    """Seed sample newspaper sources."""
    with app.app_context():
        sources = [
            Source(
                name="Deccan Herald (Karnataka Edition)",
                base_url="https://www.deccanherald.com/notices",
                source_type="html",
                scrape_frequency_minutes=60,
                selectors_config={"article_selector": ".public-notices a, .notice-item a"}
            ),
            Source(
                name="The Hindu (Legal Notices & Classifieds)",
                base_url="https://www.thehindu.com/notices",
                source_type="html",
                scrape_frequency_minutes=60,
                selectors_config={"article_selector": ".legal-notice a"}
            ),
            Source(
                name="Times of India Property Legal Gazette",
                base_url="https://timesofindia.indiatimes.com/legal-notices",
                source_type="pdf",
                scrape_frequency_minutes=120
            ),
            Source(
                name="Eenadu Andhra & Telangana Regional ePaper",
                base_url="https://epaper.eenadu.net/notices",
                source_type="image",
                scrape_frequency_minutes=180
            ),
            Source(
                name="Dina Thanthi Tamil Nadu Legal Gazette",
                base_url="https://www.dailythanthi.com/notices",
                source_type="mixed",
                scrape_frequency_minutes=120
            )
        ]
        for s in sources:
            existing = Source.query.filter_by(base_url=s.base_url).first()
            if not existing:
                db.session.add(s)
        db.session.commit()
        click.echo('Sources seeded successfully.')

@app.cli.command("create-client")
@click.argument('name')
@click.argument('email')
@click.option('--password', default='admin123', help='Password for web login')
def create_client(name, email, password):
    """Create a new client with API key and web password."""
    with app.app_context():
        client = Client(name=name, email=email, plan_tier='enterprise')
        client.set_password(password)
        db.session.add(client)
        db.session.commit()
        click.echo(f'Client {name} created with API key: {client.api_key} and password: {password}')

@app.cli.command("seed-demo")
def seed_demo():
    """Seed full enterprise demo dataset with admin user, sources, disputes, notices, and alerts."""
    with app.app_context():
        db.create_all()
        
        # Clear existing to ensure clean, accurate state
        Alert.query.delete()
        Subscription.query.delete()
        Dispute.query.delete()
        ExtractedNotice.query.delete()
        RawArticle.query.delete()
        Source.query.delete()
        db.session.commit()
        
        # 1. Admin user
        admin = Client.query.filter_by(email="admin@landwatch.com").first()
        if not admin:
            admin = Client(
                name="Vikramaditya Singhania",
                email="admin@landwatch.com",
                company="Apex Prime Real Estate Fund & Analytics",
                plan_tier="enterprise"
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.flush()
            click.echo("Created admin user: admin@landwatch.com / admin123")
            
        # 2. Monitored Newspaper Sources
        sources_list = [
            Source(
                name="Deccan Herald (Bengaluru Metro Edition)",
                base_url="https://www.deccanherald.com/notices/bengaluru",
                source_type="html",
                scrape_frequency_minutes=60,
                selectors_config={"article_selector": ".public-notices a, .notice-item a"},
                last_scraped_at=datetime.utcnow() - timedelta(minutes=15)
            ),
            Source(
                name="The Hindu (South Legal & Property Plus)",
                base_url="https://www.thehindu.com/notices/legal-chennai",
                source_type="pdf",
                scrape_frequency_minutes=60,
                selectors_config={"article_selector": ".legal-notice a"},
                last_scraped_at=datetime.utcnow() - timedelta(minutes=45)
            ),
            Source(
                name="Eenadu (Hyderabad & Ranga Reddy ePaper)",
                base_url="https://epaper.eenadu.net/notices/hyderabad",
                source_type="image",
                scrape_frequency_minutes=120,
                selectors_config={"article_selector": ".epaper-notice a"},
                last_scraped_at=datetime.utcnow() - timedelta(hours=1, minutes=20)
            ),
            Source(
                name="Times of India (Realty Legal Gazette)",
                base_url="https://timesofindia.indiatimes.com/legal-notices/bengaluru",
                source_type="pdf",
                scrape_frequency_minutes=180,
                last_scraped_at=datetime.utcnow() - timedelta(hours=2)
            ),
            Source(
                name="Prajavani (Karnataka State District Edition)",
                base_url="https://www.prajavani.net/notices/karnataka",
                source_type="mixed",
                scrape_frequency_minutes=120,
                last_scraped_at=datetime.utcnow() - timedelta(hours=3)
            )
        ]
        for s in sources_list:
            db.session.add(s)
        db.session.flush()

        # 3. Comprehensive Indian Land Dispute Dataset
        disputes_catalog = [
            {
                "title": "Public Notice: Disputed Sale Deed & Injunction on Sy No. 142/2 Kadugodi",
                "url": "https://www.deccanherald.com/notices/2026/08/kadugodi-dispute-142",
                "location": "Kadugodi, Whitefield, Bengaluru East, Karnataka",
                "dispute_type": "Ownership Title Dispute",
                "parties": ["Ramesh Kumar Reddy (Petitioner)", "M/s Prestige Horizon Ventures Ltd (Respondent 1)", "Siddharth Rao (Respondent 2)"],
                "survey_no": "Sy No. 142/2",
                "property_no": "Khata No. 892/142 (A-Khata BBMP)",
                "severity": "critical",
                "urgency": 9,
                "status": "active",
                "cluster_id": "CLU-BLR-WHT-142",
                "valuation_inr": "₹28.50 Cr",
                "land_extent": "3 Acres 15 Guntas",
                "north": "Sy No. 141/1 Private Layout",
                "south": "80ft ITPL-Kadugodi Main Road",
                "east": "Channasandra Lake Buffer Zone",
                "west": "Sy No. 142/3 Tech Zone",
                "summary": "Original Suit O.S. No. 4521/2026 before the City Civil Court, Bengaluru. Petitioner claims fraudulent execution of registered GPA and subsequent sale deed without legal heirs' consent. Temporary injunction granted under Order 39 Rule 1 & 2 CPC restraining construction and third-party conveyance.",
                "ocr_text": "PUBLIC LEGAL NOTICE: Take notice that our client Shri Ramesh Kumar Reddy has instituted Original Suit O.S. No. 4521/2026 before the Hon'ble City Civil Court at Bengaluru against M/s Prestige Horizon Ventures Ltd and Siddharth Rao in respect of schedule immovable property bearing Survey No. 142/2, situated at Kadugodi Village, Bidarahalli Hobli, Bengaluru East Taluk measuring 3 Acres 15 Guntas. The Hon'ble Court has granted an ad-interim order of status quo. General public and financial institutions are hereby cautioned against entering into any sale, mortgage, development agreement, lease or commercial financial transactions.",
                "authority": "City Civil Court, Bengaluru (CCH-24)"
            },
            {
                "title": "Partition Suit & Construction Stay: Sy No. 45/1A Gachibowli Financial District",
                "url": "https://epaper.eenadu.net/notices/2026/08/gachibowli-partition-45",
                "location": "Gachibowli Financial District, Hyderabad, Telangana",
                "dispute_type": "Partition & Succession Dispute",
                "parties": ["K. Venkateshwar Rao & Legal Heirs", "Urban Horizon Towers LLP", "T. Sudhakar Reddy"],
                "survey_no": "Sy No. 45/1A & 45/1B",
                "property_no": "TSIIC Allotment Plot Nos. 12-15",
                "severity": "critical",
                "urgency": 9,
                "status": "active",
                "cluster_id": "CLU-HYD-GCB-45",
                "valuation_inr": "₹82.00 Cr",
                "land_extent": "4 Acres 20 Guntas",
                "north": "100ft Financial District Ring Road",
                "south": "Sy No. 46 TSIIC IT SEZ",
                "east": "Nanakramguda Commercial Corridor",
                "west": "Kokapet Link Road",
                "summary": "Suit for Partition and Separate Possession O.S. No. 789/2026 pending before the Senior Civil Judge Court, Ranga Reddy District. Coparceners dispute ancestral partition deed dated 2012 alleging forgery of signatures and unrecorded settlement deed for multi-storey IT commercial development.",
                "ocr_text": "NOTICE OF PENDING LITIGATION & CAVEAT: Notice is hereby given to the general public, developers, and corporate entities that a Partition Suit O.S. No. 789/2026 along with I.A. No. 1/2026 for injunction is pending before the Hon'ble Senior Civil Judge, Ranga Reddy at L.B. Nagar. Schedule Property: Land in Sy No. 45/1A & 45/1B, Serilingampally Mandal, Gachibowli. Any development or encumbrance created will be hit by Doctrine of Lis Pendens under Section 52 of Transfer of Property Act.",
                "authority": "Senior Civil Judge Court, Ranga Reddy Dist"
            },
            {
                "title": "SARFAESI Debt Recovery & Symbolic Possession: Guindy Industrial Estate",
                "url": "https://www.thehindu.com/notices/2026/08/guindy-mortgage-claim",
                "location": "Guindy Industrial Estate, Chennai, Tamil Nadu",
                "dispute_type": "Mortgage & SARFAESI Dispute",
                "parties": ["Apex Industrial Finance Corporation", "Sunland Estates LLP (Borrower)", "K. Rajendran (Guarantor)"],
                "survey_no": "Town Survey No. 88/4",
                "property_no": "Industrial Plot B-12, Block 3",
                "severity": "high",
                "urgency": 8,
                "status": "active",
                "cluster_id": "CLU-CHN-GND-88",
                "valuation_inr": "₹45.00 Cr",
                "land_extent": "2.40 Acres",
                "north": "SIDCO Industrial Road",
                "south": "Railway Feeder Line",
                "east": "Plot B-11 Auto Components",
                "west": "Guindy Inner Ring Road",
                "summary": "Possession Notice under SARFAESI Act Sec 13(4) issued by Authorized Officer against unpaid credit facilities amounting to ₹38.4 Cr. Physical auction process initiated before Debt Recovery Tribunal (DRT-1) Chennai.",
                "ocr_text": "POSSESSION NOTICE (For Immovable Property): Whereas the Authorized Officer of Apex Industrial Finance Corp under SARFAESI Act 2002 issued Demand Notice dated 12/01/2026 calling upon Sunland Estates LLP to repay Rs. 38,42,10,500/-. The borrower having failed, notice is hereby given that the undersigned has taken Symbolic Possession of T.S. No. 88/4, Block 3, Guindy. General public is warned not to deal with this property.",
                "authority": "Debt Recovery Tribunal (DRT-1), Chennai"
            },
            {
                "title": "Government Land Acquisition Sec 28(1) Objection: Sarjapur Road Peripheral Ring",
                "url": "https://www.deccanherald.com/notices/2026/08/sarjapur-acquisition-98",
                "location": "Dommasandra, Sarjapur Road, Anekal Taluk, Bengaluru",
                "dispute_type": "Land Acquisition Objection",
                "parties": ["KIADB (State Agency)", "Sarjapur Land Owners Action Committee", "B.M. Muniyappa"],
                "survey_no": "Sy No. 98/3 & 98/4",
                "property_no": "Revenue Assessment No. 430/98",
                "severity": "medium",
                "urgency": 6,
                "status": "monitoring",
                "cluster_id": "CLU-BLR-SRJ-98",
                "valuation_inr": "₹16.80 Cr",
                "land_extent": "5 Acres 10 Guntas",
                "north": "Sy No. 97 Panchayat Road",
                "south": "Proposed PRR 100m Right of Way",
                "east": "Dommasandra Village Boundary",
                "west": "Sy No. 99 Private Farmland",
                "summary": "Objections filed under Section 28(2) of KIAD Act 1966 challenging preliminary notification for industrial park corridor and demanding market compensation under RFCTLARR Act 2013.",
                "ocr_text": "PUBLIC NOTICE UNDER SECTION 28(2) KIAD ACT: Notice is hereby given regarding proposed acquisition of land in Survey Nos. 98/3 and 98/4, Dommasandra Village, Sarjapur Hobli, Anekal Taluk for industrial development. Landowners are called upon to appear for enquiry on 15/09/2026 before Special Land Acquisition Officer.",
                "authority": "Special Land Acquisition Officer, KIADB Bengaluru"
            },
            {
                "title": "General Power of Attorney (GPA) Revocation: Bellandur Outer Ring Road",
                "url": "https://www.deccanherald.com/notices/2026/08/bellandur-cancellation-202",
                "location": "Bellandur ORR, Bengaluru South, Karnataka",
                "dispute_type": "Breach of Agreement",
                "parties": ["G. Narayanaswamy Naidu (Owner)", "Ananya Prime Builders Pvt Ltd (Developer)"],
                "survey_no": "Sy No. 202/1 & 202/3",
                "property_no": "BDA Khata No. 512/202",
                "severity": "high",
                "urgency": 8,
                "status": "active",
                "cluster_id": "CLU-BLR-BLD-202",
                "valuation_inr": "₹54.00 Cr",
                "land_extent": "1 Acre 38 Guntas",
                "north": "Bellandur Lake Regulatory Buffer",
                "south": "Outer Ring Road Service Lane",
                "east": "Cessna Business Park Entry",
                "west": "Sy No. 203 Tech Campus",
                "summary": "Public notice of unilateral cancellation and revocation of Joint Development Agreement (JDA) and General Power of Attorney executed in 2021 due to builder's failure to obtain RERA approvals and commercial default.",
                "ocr_text": "PUBLIC NOTICE OF CANCELLATION OF GPA & JDA: Notice is hereby given to the general public, prospective flat purchasers and financial institutions that the registered General Power of Attorney Doc No. 4521/2021 and Joint Development Agreement in respect of Sy No. 202/1, Bellandur, is hereby CANCELLED and REVOKED with immediate effect. Any transaction entered with Ananya Builders is void ab initio.",
                "authority": "Sub-Registrar Office, Shivajinagar"
            },
            {
                "title": "Encroachment Demarcation & Survey Verification: OMR Sholinganallur",
                "url": "https://www.thehindu.com/notices/2026/08/omr-boundary-dispute",
                "location": "Sholinganallur, OMR IT Highway, Chennai, Tamil Nadu",
                "dispute_type": "Boundary Encroachment",
                "parties": ["V. Natarajan & Sons", "Apex IT Infra Developers Ltd"],
                "survey_no": "Survey No. 312/5",
                "property_no": "Patta No. 1823/2022",
                "severity": "low",
                "urgency": 3,
                "status": "resolved",
                "cluster_id": "CLU-CHN-OMR-312",
                "valuation_inr": "₹12.50 Cr",
                "land_extent": "1.10 Acres",
                "north": "OMR Service Road",
                "south": "Buckingham Canal Buffer",
                "east": "IT SEZ Boundary Wall",
                "west": "Survey No. 312/4",
                "summary": "Boundary dispute regarding 15-cent strip amicably settled following joint survey and verification by Tahsildar Tambaram Taluk and updated FMB sketch.",
                "ocr_text": "PUBLIC INTIMATION OF COMPLETED SURVEY: Notice is given that the boundary demarcation for Survey No. 312/5, Sholinganallur Village, Tambaram Taluk, stands completed pursuant to Revenue Department Order. The western boundary alignment is resolved as per Field Measurement Book (FMB).",
                "authority": "Tahsildar Office, Tambaram Taluk"
            },
            {
                "title": "Lis Pendens Notice: Kokapet Neopolis Golden Mile Land",
                "url": "https://epaper.eenadu.net/notices/2026/08/kokapet-neopolis-dispute",
                "location": "Kokapet Neopolis, Hyderabad, Telangana",
                "dispute_type": "Ownership Title Dispute",
                "parties": ["Smt. Chandrakala & Heirs", "Hyderabad Megapolis Infra Corp", "HMDA"],
                "survey_no": "Sy No. 239/P & 240/P",
                "property_no": "Neopolis Commercial Plot 8",
                "severity": "critical",
                "urgency": 9,
                "status": "active",
                "cluster_id": "CLU-HYD-KKP-239",
                "valuation_inr": "₹140.00 Cr",
                "land_extent": "6 Acres 00 Guntas",
                "north": "Neopolis 120ft Radial Road",
                "south": "Outer Ring Road Toll Corridor",
                "east": "Golden Mile IT Towers",
                "west": "Gandipet Water Body Zone",
                "summary": "Writ Petition W.P. No. 12904/2026 before the High Court for the State of Telangana challenging HMDA e-auction allotment and claiming ancestral inam title. Caveat entered by state government.",
                "ocr_text": "LEGAL NOTICE & WARNING TO PROSPECTIVE BUYERS: Take notice that Writ Petition W.P. No. 12904/2026 is pending before the Hon'ble High Court of Telangana challenging the layout sanction and auction of Sy Nos. 239/P & 240/P, Kokapet Village, Gandipet Mandal. Any development is subject to the final outcome of the Writ Petition.",
                "authority": "High Court for the State of Telangana"
            },
            {
                "title": "Will Probate & Succession Challenge: Devanahalli Airport Road",
                "url": "https://www.deccanherald.com/notices/2026/08/devanahalli-probate-77",
                "location": "Devanahalli, Airport Expressway, Bengaluru Rural, Karnataka",
                "dispute_type": "Partition & Succession Dispute",
                "parties": ["Dr. Anirudh Bharadwaj", "Sunita Bharadwaj (Sister)", "AeroCity Realty Ventures"],
                "survey_no": "Sy No. 77/1 & 77/2",
                "property_no": "Gramatana Assessment No. 104",
                "severity": "high",
                "urgency": 7,
                "status": "active",
                "cluster_id": "CLU-BLR-DEV-77",
                "valuation_inr": "₹34.00 Cr",
                "land_extent": "4 Acres 18 Guntas",
                "north": "Airport Link Expressway",
                "south": "Sy No. 76 KIADB Aerospace SEZ",
                "east": "Binnamangala Village Lake",
                "west": "Sy No. 78 Private Farmland",
                "summary": "Probate Petition P&SC No. 331/2026 before Principal District Judge Bengaluru Rural. Disputing daughter challenges registered Will dated 2019 alleged to have been executed under undue influence for prime airport corridor land.",
                "ocr_text": "NOTICE OF WILL PROBATE PETITION: Notice is hereby given under Section 283 of Indian Succession Act that P&SC No. 331/2026 has been filed before Principal District Judge at Devanahalli regarding property bearing Sy No. 77/1, Devanahalli Hobli. Any person claiming interest must file citations within 30 days.",
                "authority": "Principal District & Sessions Court, Bengaluru Rural"
            }
        ]

        import hashlib
        for data in disputes_catalog:
            url_hash = hashlib.sha256(data["url"].encode()).hexdigest()
            raw_art = RawArticle(
                source_id=sources_list[0].id,
                url=data["url"],
                url_hash=url_hash,
                title=data["title"],
                raw_text=data["ocr_text"],
                publish_date=datetime.utcnow() - timedelta(days=2),
                scrape_status="scraped"
            )
            db.session.add(raw_art)
            db.session.flush()
            
            notice = ExtractedNotice(
                raw_article_id=raw_art.id,
                notice_type=data["dispute_type"],
                property_number=data["property_no"],
                survey_number=data["survey_no"],
                disputing_parties=data["parties"],
                location=data["location"],
                notice_date=datetime.utcnow() - timedelta(days=2),
                issuing_authority=data["authority"],
                ocr_text=data["ocr_text"],
                ocr_confidence_scores={"overall": 0.96, "survey_number": 0.98, "parties": 0.95, "court": 0.99},
                needs_manual_review=(data["severity"] == "critical"),
                processing_status="processed"
            )
            db.session.add(notice)
            db.session.flush()
            
            dispute = Dispute(
                extracted_notice_id=notice.id,
                dispute_type=data["dispute_type"],
                location=data["location"],
                parties_involved=data["parties"],
                urgency_score=data["urgency"],
                severity=data["severity"],
                status=data["status"],
                summary=data["summary"],
                cluster_id=data["cluster_id"],
                raw_llm_response={
                    "dispute_type": data["dispute_type"],
                    "location": data["location"],
                    "parties": data["parties"],
                    "urgency_score": data["urgency"],
                    "severity": data["severity"],
                    "valuation_inr": data["valuation_inr"],
                    "land_extent": data["land_extent"],
                    "north_boundary": data["north"],
                    "south_boundary": data["south"],
                    "east_boundary": data["east"],
                    "west_boundary": data["west"],
                    "summary": data["summary"]
                }
            )
            db.session.add(dispute)
            db.session.flush()

        # 4. Subscriptions for Admin User
        sub1 = Subscription(
            client_id=admin.id,
            tracked_regions=["Bengaluru", "Whitefield", "Sarjapur", "Devanahalli", "Bellandur"],
            tracked_properties=["Sy No. 142/2", "Sy No. 202/1", "Sy No. 98/3", "Sy No. 77/1"],
            min_severity="medium",
            notification_method="both",
            webhook_url="https://api.apexrealtyfund.com/webhooks/landwatch-alerts",
            is_active=True
        )
        db.session.add(sub1)
        
        sub2 = Subscription(
            client_id=admin.id,
            tracked_regions=["Hyderabad", "Gachibowli", "Kokapet", "Financial District"],
            tracked_properties=["Sy No. 45/1A", "Sy No. 239/P"],
            min_severity="high",
            notification_method="email",
            is_active=True
        )
        db.session.add(sub2)

        sub3 = Subscription(
            client_id=admin.id,
            tracked_regions=["Chennai", "Guindy", "Sholinganallur", "OMR"],
            tracked_properties=["Town Survey No. 88/4"],
            min_severity="high",
            notification_method="both",
            webhook_url="https://api.apexrealtyfund.com/webhooks/chennai-legal",
            is_active=True
        )
        db.session.add(sub3)
        db.session.flush()

        # 5. Real-Time Dispatched Alerts
        all_disputes = Dispute.query.order_by(Dispute.urgency_score.desc()).all()
        for idx, disp in enumerate(all_disputes[:5]):
            alert = Alert(
                client_id=admin.id,
                dispute_id=disp.id,
                subscription_id=sub1.id if 'Bengaluru' in (disp.location or '') else (sub2.id if 'Hyderabad' in (disp.location or '') else sub3.id),
                alert_type="new_dispute" if idx % 2 == 0 else "status_change",
                message=f"CRITICAL LEGAL ALERT: {disp.severity.upper()} dispute detected on {disp.extracted_notice.survey_number} in {disp.location}. {disp.summary[:100]}...",
                is_read=(idx >= 3),
                delivered_at=datetime.utcnow() - timedelta(minutes=idx * 25 + 10),
                delivery_status="sent"
            )
            db.session.add(alert)
            
        db.session.commit()
        click.echo('Enterprise dataset seeded successfully! Login: admin@landwatch.com / admin123')

if __name__ == '__main__':
    app.cli()
