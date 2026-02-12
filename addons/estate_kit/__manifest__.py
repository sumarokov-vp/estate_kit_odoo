{
    "name": "Estate Kit",
    "version": "19.0.1.2.0",
    "category": "Real Estate",
    "summary": "Manage real estate properties",
    "description": """
        Estate Kit module for managing real estate properties.

        Features:
        - Property management with 56+ attributes
        - Cities, districts and streets lookups
        - CRM integration for deals
        - Role-based access control
    """,
    "author": "Estate Kit Team",
    "website": "",
    "license": "LGPL-3",
    "depends": ["base", "base_setup", "mail", "crm"],
    "data": [
        "security/estate_security.xml",
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "data/estate_city_data.xml",
        "data/estate_climate_equipment_data.xml",
        "data/estate_appliance_data.xml",
        "views/estate_city_views.xml",
        "views/estate_district_views.xml",
        "views/estate_street_views.xml",
        "views/estate_source_views.xml",
        "views/estate_climate_equipment_views.xml",
        "views/estate_appliance_views.xml",
        "views/estate_property_views.xml",
        "views/crm_lead_views.xml",
        "views/res_config_settings_views.xml",
        "views/estate_menus.xml",
        "wizards/krisha_parser_views.xml",
    ],
    "demo": [],
    "assets": {
        "web.assets_backend": [
            "estate_kit/static/src/fields/*.js",
            "estate_kit/static/src/fields/*.xml",
            "estate_kit/static/src/components/**/*.js",
            "estate_kit/static/src/components/**/*.xml",
            "estate_kit/static/src/components/**/*.scss",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
    "post_init_hook": "post_init_hook",
}
