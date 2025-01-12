from shiny import ui

def main_plots_card():
    return ui.card(
            ui.card("First plot"),
            ui.card("Second plot")
        
    )