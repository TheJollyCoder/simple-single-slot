def refresh_species_dropdown(app):
    if hasattr(app, "species_dropdown"):
        app.species_dropdown["values"] = list(app.rules.keys())
