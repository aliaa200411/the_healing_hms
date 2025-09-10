{
    "name": "Hospital Backend Theme",
    "version": "18.0.1.0.0",
    "summary": "Custom backend theme for hospital UI",
    "description": "Change backend look: colors, navbar, sidebar, cards, forms, kanban, lists.",
    "author": "Maryam shqeer",
    "category": "Theme/Backend",
    "depends": ["web"],
    "data": [
        "views/assets.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hospital_theme/static/src/css/custom_backend.css",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
