import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.database import engine, SessionLocal, Base
from models.legal_research import LegalCase, ResearchQuery, SavedCase
from models.user import User
from models.workflow import Workflow
from models.audit import AuditLog
import uuid

def seed_legal_cases():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if cases already exist
        if db.query(LegalCase).first():
            print("Legal cases already seeded.")
            return

        cases = [
            {
                "title": "Amazon GDPR Violation",
                "court": "CNPD (Luxembourg)",
                "jurisdiction": "European Union",
                "year": 2021,
                "regulation": "GDPR",
                "summary": "Fined €746,000,000 by CNPD for Non-compliance with GDPR principles related to targeted advertising.",
                "full_text": "The Luxembourg data protection authority (CNPD) issued a record fine against Amazon Europe Core S.à r.l. for its processing of personal data for behavioral advertising purposes in violation of the GDPR. The case highlighted the importance of valid consent for tracking and profiling.",
                "key_ruling": "Record GDPR fine for unlawful targeted advertising profiling."
            },
            {
                "title": "TikTok GDPR Violation",
                "court": "Data Protection Commission (Ireland)",
                "jurisdiction": "European Union",
                "year": 2023,
                "regulation": "GDPR",
                "summary": "Fined €345,000,000 by DPC for Violations related to children's data and dark patterns.",
                "full_text": "Ireland's DPC penalized TikTok for failing to protect the privacy of children using its platform, including default public settings for accounts and the use of 'dark patterns' that nudged users towards less privacy-friendly options.",
                "key_ruling": "Significant fine for children's privacy violations and dark pattern usage."
            },
            {
                "title": "Sephora CCPA Violation",
                "court": "California Office of the Attorney General",
                "jurisdiction": "USA - California",
                "year": 2022,
                "regulation": "CCPA",
                "summary": "Fined $1,200,000 by OAG for CCPA violation for selling customer data without opt-out notice.",
                "full_text": "The California Attorney General announced a settlement with Sephora, Inc. for failing to disclose it was selling personal information, failing to process opt-out requests via Global Privacy Control, and failing to cure violations within the 30-day period.",
                "key_ruling": "First major CCPA enforcement action regarding the sale of personal data."
            },
            {
                "title": "British Airways GDPR Violation",
                "court": "Information Commissioner's Office (UK)",
                "jurisdiction": "United Kingdom",
                "year": 2020,
                "regulation": "GDPR",
                "summary": "Fined £20,000,000 by ICO for Data breach notification failure and poor security affecting 400k customers.",
                "full_text": "The ICO fined British Airways after the personal and financial details of more than 400,000 customers were compromised in a 2018 cyberattack. The investigation found that BA was processing a significant amount of data without adequate security measures.",
                "key_ruling": "Substantial fine for insufficient technical and organizational security measures."
            },
            {
                "title": "H&M GDPR Violation",
                "court": "BfDI (Germany)",
                "jurisdiction": "European Union",
                "year": 2020,
                "regulation": "GDPR",
                "summary": "Fined €35,258,707 by BfDI for Illegal surveillance of employees in Nuremberg service center.",
                "full_text": "The German data protection authority fined H&M for extensively monitoring employees' private lives at its service center in Nuremberg, including recording details about family issues, religious beliefs, and health history.",
                "key_ruling": "Major penalty for intrusive employee monitoring and lack of data minimization."
            },
            {
                "title": "Planet49 GmbH v Bundesverband",
                "court": "European Court of Justice (ECJ)",
                "jurisdiction": "European Union",
                "year": 2019,
                "regulation": "GDPR",
                "summary": "The court ruled that pre-ticked consent boxes do not constitute valid consent under GDPR. Consent must be active and freely given.",
                "full_text": "In Case C-673/17, the Court of Justice of the European Union ruled that Article 6(1)(a) of Regulation 2016/679 (GDPR) must be interpreted as meaning that consent is not validly constituted by way of a pre-ticked checkbox which the user must deselect to refuse his consent.",
                "key_ruling": "Pre-ticked checkboxes are invalid for GDPR consent; explicit action is required."
            },
            {
                "title": "Schrems II (Data Protection Commissioner v Facebook Ireland Ltd)",
                "court": "European Court of Justice (ECJ)",
                "jurisdiction": "European Union",
                "year": 2020,
                "regulation": "GDPR",
                "summary": "Invalidated the EU-US Privacy Shield due to concerns about US surveillance programs and insufficient protection for EU data subjects.",
                "full_text": "The court found that US law does not provide data protection equivalent to GDPR. Standard Contractual Clauses (SCCs) remain valid but require additional safeguards if the destination country lacks adequate protections.",
                "key_ruling": "EU-US Privacy Shield invalidated; SCCs require 'supplementary measures'."
            }
        ]

        for case_data in cases:
            db_case = LegalCase(**case_data)
            db.add(db_case)
        
        db.commit()
        print(f"Successfully seeded {len(cases)} legal cases.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_legal_cases()
