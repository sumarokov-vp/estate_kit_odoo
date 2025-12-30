{
    "name": "Royal Estate",
    "version": "19.0.1.0.0",
    "category": "Real Estate",
    "summary": "Manage real estate properties",
    "description": """
        Royal Estate module for managing real estate properties.

        Features:
        - Property management with EAV attributes
        - Districts and sources lookups
        - CRM integration for deals
        - Role-based access control
    """,
    "author": "Royal Estate Team",
    "website": "",
    "license": "LGPL-3",
    "depends": ["base", "mail", "crm"],
    "data": [
        "security/estate_security.xml",
        "security/ir.model.access.csv",
        "views/estate_district_views.xml",
        "views/estate_source_views.xml",
        "views/estate_attribute_views.xml",
        "views/estate_property_views.xml",
        "views/crm_lead_views.xml",
        "views/estate_menus.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
    "post_init_hook": "post_init_hook",
}
