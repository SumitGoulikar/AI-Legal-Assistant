# backend/create_templates.py
import json
import os
from pathlib import Path

# Ensure templates directory exists
TEMPLATE_DIR = Path("templates")
TEMPLATE_DIR.mkdir(exist_ok=True)

templates = [
    {
        "name": "Residential Rental Agreement",
        "slug": "rental_agreement",
        "category": "agreements",
        "description": "Standard 11-month rental agreement for residential property.",
        "applicable_laws": ["Rent Control Act", "Transfer of Property Act, 1882"],
        "form_schema": {
            "fields": [
                {"name": "landlord_name", "label": "Landlord Name", "type": "text"},
                {"name": "tenant_name", "label": "Tenant Name", "type": "text"},
                {"name": "property_address", "label": "Property Address", "type": "textarea"},
                {"name": "rent_amount", "label": "Monthly Rent (INR)", "type": "number"},
                {"name": "deposit_amount", "label": "Security Deposit (INR)", "type": "number"},
                {"name": "start_date", "label": "Lease Start Date", "type": "date"},
                {"name": "notice_period", "label": "Notice Period (Months)", "type": "select", "options": ["1", "2", "3"]}
            ]
        },
        "template_body": """RENTAL AGREEMENT

This Rental Agreement is made on this {{start_date}} by and between:

{{landlord_name}} (hereinafter referred to as the "LESSOR"),
AND
{{tenant_name}} (hereinafter referred to as the "LESSEE").

1. PROPERTY
The Lessor hereby lets out the property situated at: {{property_address}}.

2. RENT AND DEPOSIT
The Lessee shall pay a monthly rent of INR {{rent_amount}} on or before the 5th of every month.
The Lessee has paid a Security Deposit of INR {{deposit_amount}}, which is refundable at the time of vacating.

3. TERM
This lease is valid for a period of 11 months starting from {{start_date}}.

4. NOTICE PERIOD
Either party may terminate this agreement by giving {{notice_period}} month(s) written notice.

IN WITNESS WHEREOF, the parties have signed this agreement.

Lessor: _________________      Lessee: _________________"""
    },
    {
        "name": "Employment Offer Letter",
        "slug": "employment_agreement",
        "category": "contracts",
        "description": "Formal job offer letter outlining salary, role, and terms.",
        "applicable_laws": ["Indian Contract Act, 1872", "Industrial Disputes Act"],
        "form_schema": {
            "fields": [
                {"name": "company_name", "label": "Company Name", "type": "text"},
                {"name": "employee_name", "label": "Employee Name", "type": "text"},
                {"name": "designation", "label": "Job Title", "type": "text"},
                {"name": "salary", "label": "Annual CTC (INR)", "type": "number"},
                {"name": "joining_date", "label": "Joining Date", "type": "date"},
                {"name": "probation_months", "label": "Probation Period (Months)", "type": "number"}
            ]
        },
        "template_body": """OFFER OF EMPLOYMENT

Date: {{joining_date}}

To,
{{employee_name}}

Dear {{employee_name}},

We are pleased to offer you the position of {{designation}} at {{company_name}}.

1. COMPENSATION
Your Annual Cost to Company (CTC) will be INR {{salary}}. Detailed breakup will be provided upon joining.

2. PROBATION
You will be on a probation period of {{probation_months}} months from the date of joining.

3. JOINING
You are requested to join us on or before {{joining_date}}.

We look forward to having you on our team.

For {{company_name}},

_____________________
Authorized Signatory"""
    },
    {
        "name": "Freelance Service Agreement",
        "slug": "freelance_contract",
        "category": "contracts",
        "description": "Contract for hiring a freelancer or consultant.",
        "applicable_laws": ["Indian Contract Act, 1872"],
        "form_schema": {
            "fields": [
                {"name": "client_name", "label": "Client Name", "type": "text"},
                {"name": "freelancer_name", "label": "Freelancer Name", "type": "text"},
                {"name": "project_name", "label": "Project Name", "type": "text"},
                {"name": "total_fee", "label": "Total Fee (INR)", "type": "number"},
                {"name": "deadline", "label": "Completion Deadline", "type": "date"}
            ]
        },
        "template_body": """SERVICE AGREEMENT

This Agreement is made between {{client_name}} ("Client") and {{freelancer_name}} ("Contractor").

1. SCOPE OF WORK
The Contractor agrees to perform services for the project: {{project_name}}.

2. PAYMENT
The Client agrees to pay a total fee of INR {{total_fee}} upon completion.

3. DEADLINE
The services must be completed by {{deadline}}.

4. INTELLECTUAL PROPERTY
Upon full payment, the Client shall own all rights to the work produced.

Signed:

Client: _________________      Contractor: _________________"""
    },
    {
        "name": "Legal Notice (Money Recovery)",
        "slug": "legal_notice_recovery",
        "category": "notices",
        "description": "Formal notice to recover dues or outstanding payments.",
        "applicable_laws": ["Civil Procedure Code", "Negotiable Instruments Act"],
        "form_schema": {
            "fields": [
                {"name": "sender_name", "label": "Sender Name", "type": "text"},
                {"name": "recipient_name", "label": "Recipient Name", "type": "text"},
                {"name": "amount_due", "label": "Amount Due (INR)", "type": "number"},
                {"name": "reason", "label": "Reason for Due", "type": "textarea"},
                {"name": "days_to_pay", "label": "Days to Pay", "type": "number", "default_value": "15"}
            ]
        },
        "template_body": """LEGAL NOTICE

From:
Advocate for {{sender_name}}

To:
{{recipient_name}}

Subject: NOTICE FOR RECOVERY OF DUES OF INR {{amount_due}}

Sir/Madam,

Under instructions from my client {{sender_name}}, I hereby state:

1. That you owe my client a sum of INR {{amount_due}} regarding {{reason}}.
2. That despite repeated reminders, you have failed to pay the said amount.

I hereby call upon you to pay the sum of INR {{amount_due}} within {{days_to_pay}} days of receipt of this notice, failing which my client shall be constrained to initiate legal proceedings against you.

Yours faithfully,

_____________________
Advocate Signature"""
    },
    {
        "name": "General Power of Attorney",
        "slug": "power_of_attorney",
        "category": "deeds",
        "description": "Authorizing someone to act on your behalf.",
        "applicable_laws": ["Power of Attorney Act, 1882"],
        "form_schema": {
            "fields": [
                {"name": "principal_name", "label": "Principal (You)", "type": "text"},
                {"name": "attorney_name", "label": "Attorney (Agent)", "type": "text"},
                {"name": "purpose", "label": "Purpose/Powers", "type": "textarea"},
                {"name": "location", "label": "Location", "type": "text"}
            ]
        },
        "template_body": """GENERAL POWER OF ATTORNEY

KNOW ALL MEN BY THESE PRESENTS that I, {{principal_name}}, do hereby appoint {{attorney_name}} as my true and lawful attorney.

To do and execute all or any of the following acts, deeds, and things on my behalf:
{{purpose}}

I hereby ratify and confirm that all acts done by my said attorney shall be binding on me as if done by myself.

Signed at {{location}}.

_____________________
{{principal_name}} (Principal)"""
    },
    {
        "name": "Last Will and Testament",
        "slug": "will",
        "category": "deeds",
        "description": "Simple will for asset distribution.",
        "applicable_laws": ["Indian Succession Act, 1925"],
        "form_schema": {
            "fields": [
                {"name": "testator_name", "label": "Your Name", "type": "text"},
                {"name": "beneficiary_name", "label": "Main Beneficiary", "type": "text"},
                {"name": "executor_name", "label": "Executor Name", "type": "text"},
                {"name": "assets", "label": "Assets Description", "type": "textarea"}
            ]
        },
        "template_body": """LAST WILL AND TESTAMENT

I, {{testator_name}}, being of sound mind, do hereby declare this to be my Last Will.

1. I revoke all prior wills and codicils.
2. I appoint {{executor_name}} as the Executor of this will.
3. I bequeath my assets described as: {{assets}} to {{beneficiary_name}}.

Signed by the Testator in the presence of witnesses.

_____________________
{{testator_name}}"""
    },
    {
        "name": "Loan Agreement",
        "slug": "loan_agreement",
        "category": "contracts",
        "description": "Personal or business loan agreement.",
        "applicable_laws": ["Indian Contract Act, 1872"],
        "form_schema": {
            "fields": [
                {"name": "lender_name", "label": "Lender Name", "type": "text"},
                {"name": "borrower_name", "label": "Borrower Name", "type": "text"},
                {"name": "amount", "label": "Loan Amount", "type": "number"},
                {"name": "interest_rate", "label": "Interest Rate (%)", "type": "number"},
                {"name": "repayment_date", "label": "Repayment Date", "type": "date"}
            ]
        },
        "template_body": """LOAN AGREEMENT

This Agreement is made between {{lender_name}} ("Lender") and {{borrower_name}} ("Borrower").

1. LOAN AMOUNT
The Lender agrees to lend the Borrower the sum of INR {{amount}}.

2. INTEREST
The loan shall bear an interest rate of {{interest_rate}}% per annum.

3. REPAYMENT
The Borrower agrees to repay the full amount along with interest by {{repayment_date}}.

Signed:

Lender: _________________      Borrower: _________________"""
    },
    {
        "name": "Website Privacy Policy",
        "slug": "privacy_policy",
        "category": "notices",
        "description": "Standard privacy policy for websites.",
        "applicable_laws": ["IT Act, 2000 (SPDI Rules)"],
        "form_schema": {
            "fields": [
                {"name": "website_name", "label": "Website Name", "type": "text"},
                {"name": "contact_email", "label": "Contact Email", "type": "email"}
            ]
        },
        "template_body": """PRIVACY POLICY for {{website_name}}

1. COLLECTION OF INFORMATION
We collect information you provide directly to us when using {{website_name}}.

2. USE OF INFORMATION
We use information to provide, maintain, and improve our services.

3. CONTACT
If you have questions about this Privacy Policy, please contact us at {{contact_email}}.

Effective Date: [Current Date]"""
    },
    {
        "name": "Internship Agreement",
        "slug": "internship_agreement",
        "category": "agreements",
        "description": "Agreement for hiring interns.",
        "applicable_laws": ["Indian Contract Act, 1872"],
        "form_schema": {
            "fields": [
                {"name": "company", "label": "Company", "type": "text"},
                {"name": "intern", "label": "Intern Name", "type": "text"},
                {"name": "duration", "label": "Duration (Months)", "type": "number"},
                {"name": "stipend", "label": "Stipend (INR)", "type": "number"}
            ]
        },
        "template_body": """INTERNSHIP AGREEMENT

Between {{company}} and {{intern}}.

1. ROLE
You are hired as an Intern for a period of {{duration}} months.

2. STIPEND
You will receive a monthly stipend of INR {{stipend}}.

3. CONFIDENTIALITY
You agree to keep all company information confidential.

For {{company}}: _________________"""
    },
    {
        "name": "Partnership Deed",
        "slug": "partnership_deed",
        "category": "deeds",
        "description": "Agreement between business partners.",
        "applicable_laws": ["Indian Partnership Act, 1932"],
        "form_schema": {
            "fields": [
                {"name": "partner1", "label": "Partner 1 Name", "type": "text"},
                {"name": "partner2", "label": "Partner 2 Name", "type": "text"},
                {"name": "business_name", "label": "Business Name", "type": "text"},
                {"name": "share_ratio", "label": "Profit Share Ratio (e.g. 50:50)", "type": "text"}
            ]
        },
        "template_body": """PARTNERSHIP DEED

This Deed of Partnership is made between {{partner1}} and {{partner2}}.

1. NAME
The business shall be carried on under the name {{business_name}}.

2. PROFIT SHARING
The net profits or losses of the business shall be shared in the ratio of {{share_ratio}}.

3. DISPUTES
Any disputes shall be settled by arbitration in accordance with the Arbitration and Conciliation Act, 1996.

Partner 1: _________________      Partner 2: _________________"""
    }
]

print(f"Creating {len(templates)} templates...")

for t in templates:
    filename = f"{t['slug']}_template.json"
    filepath = TEMPLATE_DIR / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(t, f, indent=2)
    
    print(f"✅ Created: {filename}")

print("\nDone! Please restart your backend server to load these into the database.")