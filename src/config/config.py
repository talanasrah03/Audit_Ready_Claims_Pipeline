"""
Domain-based configuration system.

Goal:
Define business rules for different domains (vehicle, medical, invoice, etc.)
in one centralized place.

What this file does:
- Defines allowed claim types for each domain
- Defines validation rules (minimum and maximum amounts) for each claim type
- Allows the rest of the system to adapt its behavior depending on the domain

Important concept:
Different industries (domains) follow different business rules.

Example:
- A vehicle claim does not follow the same logic as a medical claim
- An invoice claim does not use the same limits as a logistics claim

Why this matters:
Instead of hardcoding rules directly inside validation scripts,
we keep them here in one place.

This makes the system:
- easier to update
- easier to maintain
- easier to extend with new domains later

This structure simulates real-world AI systems,
where each client or business area may have its own configuration.
"""


"""
CONFIGS:
A dictionary that stores all domain settings.

Structure:
- Key   → domain name
- Value → configuration for that domain

Example:
CONFIGS["vehicle"]
→ returns all rules for vehicle claims
"""

CONFIGS = {

    # =========================
    # VEHICLE DOMAIN
    # =========================
    "vehicle": {

        """
        Goal:
        Define all allowed claim types for vehicle-related claims.

        Logic:
        - Only these claim types are considered valid in this domain
        - Any other value should normally be flagged as unexpected or invalid

        Example:
        "Vehicle Theft" → valid
        "Hospitalization" → invalid in this domain
        """

        "claim_types": [
            "Single Vehicle Collision",
            "Multi-vehicle Collision",
            "Vehicle Theft",
            "Parked Car"
        ],

        """
        Goal:
        Define valid amount ranges for each vehicle claim type.

        Logic:
        - Each claim type has:
          - a minimum allowed amount
          - a maximum allowed amount
        - These values are later used by validation scripts
          to detect abnormal or suspicious amounts

        Example:
        Vehicle Theft:
        - min = 500
        - max = 50000

        amount = 100 → too low
        amount = 60000 → too high
        """

        "rules": [
            {"claim_type": "Vehicle Theft", "min_amount": 500, "max_amount": 50000},
            {"claim_type": "Single Vehicle Collision", "min_amount": 200, "max_amount": 30000},
            {"claim_type": "Multi-vehicle Collision", "min_amount": 1000, "max_amount": 70000},
            {"claim_type": "Parked Car", "min_amount": 50, "max_amount": 10000},
        ]
    },

    # =========================
    # MEDICAL DOMAIN
    # =========================
    "medical": {

        """
        Goal:
        Define allowed claim types for medical or healthcare-related claims.

        Logic:
        - Covers major healthcare situations such as treatment, medication, or emergency care

        Example:
        "Hospitalization" → valid
        "Vehicle Theft" → invalid in this domain
        """

        "claim_types": [
            "Hospitalization",
            "Dental Treatment",
            "Emergency Visit",
            "Medication"
        ],

        """
        Goal:
        Define realistic amount ranges for medical claims.

        Logic:
        - Some medical events can be expensive, such as hospitalization
        - Others are usually lower-cost, such as medication

        Example:
        Hospitalization:
        - can reach very high amounts

        Medication:
        - usually stays relatively low
        """

        "rules": [
            {"claim_type": "Hospitalization", "min_amount": 500, "max_amount": 100000},
            {"claim_type": "Dental Treatment", "min_amount": 50, "max_amount": 5000},
            {"claim_type": "Emergency Visit", "min_amount": 100, "max_amount": 20000},
            {"claim_type": "Medication", "min_amount": 10, "max_amount": 3000},
        ]
    },

    # =========================
    # INVOICE / FINANCE DOMAIN
    # =========================
    "invoice": {

        """
        Goal:
        Define allowed claim types for finance and invoice-related cases.

        Logic:
        - Covers billing, supplier costs, refunds, and payment penalties

        Example:
        "Supplier Invoice" → valid
        "Lost Shipment" → belongs to logistics, not invoice
        """

        "claim_types": [
            "Supplier Invoice",
            "Service Invoice",
            "Refund Request",
            "Late Payment Fee"
        ],

        """
        Goal:
        Define realistic financial ranges for invoice-related claims.

        Logic:
        - Some invoice amounts can be large, especially supplier invoices
        - Others, such as late fees, are usually much smaller

        Example:
        Supplier Invoice:
        - can go up to 200000

        Late Payment Fee:
        - usually remains low
        """

        "rules": [
            {"claim_type": "Supplier Invoice", "min_amount": 100, "max_amount": 200000},
            {"claim_type": "Service Invoice", "min_amount": 50, "max_amount": 100000},
            {"claim_type": "Refund Request", "min_amount": 10, "max_amount": 50000},
            {"claim_type": "Late Payment Fee", "min_amount": 5, "max_amount": 5000},
        ]
    },

    # =========================
    # LOGISTICS DOMAIN
    # =========================
    "logistics": {

        """
        Goal:
        Define allowed claim types for transport and shipment-related issues.

        Logic:
        - Covers problems linked to delivery, damage, customs, or lost goods

        Example:
        "Lost Shipment" → valid
        "Hospitalization" → not relevant in this domain
        """

        "claim_types": [
            "Damaged Goods",
            "Lost Shipment",
            "Delivery Delay",
            "Customs Issue"
        ],

        """
        Goal:
        Define cost ranges for logistics incidents.

        Logic:
        - Lost or damaged shipments can involve high-value losses
        - Delivery delays are usually compensated with lower amounts

        Example:
        Lost Shipment:
        - can involve major loss

        Delivery Delay:
        - usually smaller compensation
        """

        "rules": [
            {"claim_type": "Damaged Goods", "min_amount": 100, "max_amount": 100000},
            {"claim_type": "Lost Shipment", "min_amount": 200, "max_amount": 200000},
            {"claim_type": "Delivery Delay", "min_amount": 50, "max_amount": 20000},
            {"claim_type": "Customs Issue", "min_amount": 100, "max_amount": 50000},
        ]
    },

    # =========================
    # LEGAL DOMAIN
    # =========================
    "legal": {

        """
        Goal:
        Define allowed claim types for legal and contract-related disputes.

        Logic:
        - Covers disputes, compliance issues, penalties, and service breaches

        Example:
        "Contract Dispute" → valid
        "Vehicle Theft" → not relevant in this domain
        """

        "claim_types": [
            "Contract Dispute",
            "Compliance Issue",
            "Penalty Notice",
            "Service Breach"
        ],

        """
        Goal:
        Define financial impact ranges for legal issues.

        Logic:
        - Legal disputes can become very expensive
        - Smaller notices or penalties usually stay within lower limits

        Example:
        Contract Dispute:
        - can reach very high values

        Penalty Notice:
        - usually smaller amounts
        """

        "rules": [
            {"claim_type": "Contract Dispute", "min_amount": 500, "max_amount": 500000},
            {"claim_type": "Compliance Issue", "min_amount": 100, "max_amount": 100000},
            {"claim_type": "Penalty Notice", "min_amount": 50, "max_amount": 50000},
            {"claim_type": "Service Breach", "min_amount": 200, "max_amount": 200000},
        ]
    }
}