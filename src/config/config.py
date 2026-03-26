"""
Domain-based configuration system.

This file defines:
- claim types per domain
- validation rules per domain

This simulates real-world AI systems like Lynxia,
where each client/domain has different rules and logic.
"""

CONFIGS = {

    # =========================
    # vehicles  (CURRENT)
    # =========================
    "vehicle": {
        "claim_types": [
            "Single Vehicle Collision",
            "Multi-vehicle Collision",
            "Vehicle Theft",
            "Parked Car"
        ],
        "rules": [
            {"claim_type": "Vehicle Theft", "min_amount": 500, "max_amount": 50000},
            {"claim_type": "Single Vehicle Collision", "min_amount": 200, "max_amount": 30000},
            {"claim_type": "Multi-vehicle Collision", "min_amount": 1000, "max_amount": 70000},
            {"claim_type": "Parked Car", "min_amount": 50, "max_amount": 10000},
        ]
    },

    # =========================
    # HEALTHCARE / MEDICAL
    # =========================
    "medical": {
        "claim_types": [
            "Hospitalization",
            "Dental Treatment",
            "Emergency Visit",
            "Medication"
        ],
        "rules": [
            {"claim_type": "Hospitalization", "min_amount": 500, "max_amount": 100000},
            {"claim_type": "Dental Treatment", "min_amount": 50, "max_amount": 5000},
            {"claim_type": "Emergency Visit", "min_amount": 100, "max_amount": 20000},
            {"claim_type": "Medication", "min_amount": 10, "max_amount": 3000},
        ]
    },

    # =========================
    # INVOICES / FINANCE
    # =========================
    "invoice": {
        "claim_types": [
            "Supplier Invoice",
            "Service Invoice",
            "Refund Request",
            "Late Payment Fee"
        ],
        "rules": [
            {"claim_type": "Supplier Invoice", "min_amount": 100, "max_amount": 200000},
            {"claim_type": "Service Invoice", "min_amount": 50, "max_amount": 100000},
            {"claim_type": "Refund Request", "min_amount": 10, "max_amount": 50000},
            {"claim_type": "Late Payment Fee", "min_amount": 5, "max_amount": 5000},
        ]
    },

    # =========================
    # LOGISTICS / TRANSPORT
    # =========================
    "logistics": {
        "claim_types": [
            "Damaged Goods",
            "Lost Shipment",
            "Delivery Delay",
            "Customs Issue"
        ],
        "rules": [
            {"claim_type": "Damaged Goods", "min_amount": 100, "max_amount": 100000},
            {"claim_type": "Lost Shipment", "min_amount": 200, "max_amount": 200000},
            {"claim_type": "Delivery Delay", "min_amount": 50, "max_amount": 20000},
            {"claim_type": "Customs Issue", "min_amount": 100, "max_amount": 50000},
        ]
    },

    # =========================
    # LEGAL / CONTRACTS
    # =========================
    "legal": {
        "claim_types": [
            "Contract Dispute",
            "Compliance Issue",
            "Penalty Notice",
            "Service Breach"
        ],
        "rules": [
            {"claim_type": "Contract Dispute", "min_amount": 500, "max_amount": 500000},
            {"claim_type": "Compliance Issue", "min_amount": 100, "max_amount": 100000},
            {"claim_type": "Penalty Notice", "min_amount": 50, "max_amount": 50000},
            {"claim_type": "Service Breach", "min_amount": 200, "max_amount": 200000},
        ]
    }
}