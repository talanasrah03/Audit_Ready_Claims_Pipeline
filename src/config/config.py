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

CONFIGS = {
    # =========================
    # VEHICLE DOMAIN
    # =========================
    "vehicle": {
        # Allowed claim types for vehicle-related claims
        "claim_types": [
            "Single Vehicle Collision",
            "Multi-vehicle Collision",
            "Vehicle Theft",
            "Parked Car"
        ],

        # Valid amount ranges for each vehicle claim type
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
        # Allowed claim types for medical claims
        "claim_types": [
            "Hospitalization",
            "Dental Treatment",
            "Emergency Visit",
            "Medication"
        ],

        # Valid amount ranges for each medical claim type
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
        # Allowed claim types for invoice and finance claims
        "claim_types": [
            "Supplier Invoice",
            "Service Invoice",
            "Refund Request",
            "Late Payment Fee"
        ],

        # Valid amount ranges for each invoice claim type
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
        # Allowed claim types for logistics-related claims
        "claim_types": [
            "Damaged Goods",
            "Lost Shipment",
            "Delivery Delay",
            "Customs Issue"
        ],

        # Valid amount ranges for each logistics claim type
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
        # Allowed claim types for legal-related claims
        "claim_types": [
            "Contract Dispute",
            "Compliance Issue",
            "Penalty Notice",
            "Service Breach"
        ],

        # Valid amount ranges for each legal claim type
        "rules": [
            {"claim_type": "Contract Dispute", "min_amount": 500, "max_amount": 500000},
            {"claim_type": "Compliance Issue", "min_amount": 100, "max_amount": 100000},
            {"claim_type": "Penalty Notice", "min_amount": 50, "max_amount": 50000},
            {"claim_type": "Service Breach", "min_amount": 200, "max_amount": 200000},
        ]
    }
}