from dash_extensions.enrich import DashBlueprint, LogTransform
import dash_mantine_components as dmc
from automappa.components import ids
from automappa.pages.home.components import (
    sample_cards,
    upload_modal_button,
)
from automappa.pages.home.source import HomeDataSource


HEIGHT_MARGIN = 10
WIDTH_MARGIN = 10


def render(source: HomeDataSource) -> DashBlueprint:
    app = DashBlueprint(transforms=[LogTransform()])
    app.name = ids.HOME_TAB_ID
    app.icon = "line-md:home"
    app.description = "Automappa home page to upload genome binning results."
    app.title = "Automappa home"
    app.layout = dmc.NotificationsProvider(
        dmc.Container(
            [
                dmc.Space(h=HEIGHT_MARGIN, w=WIDTH_MARGIN),
                sample_cards.render(app, source),
                dmc.Space(h=HEIGHT_MARGIN, w=WIDTH_MARGIN),
                dmc.Affix(
                    upload_modal_button.render(app, source),
                    position={"bottom": HEIGHT_MARGIN, "left": WIDTH_MARGIN},
                ),
            ],
            fluid=True,
        )
    )
    return app
