import logging
import dash

from typing import Literal
from dash_extensions.enrich import DashProxy, html
import dash_mantine_components as dmc

from automappa.components import (
    metagenome_id_store,
    tasks_store,
    pages_navbar,
)

from automappa.pages.home.source import HomeDataSource
from automappa.pages.mag_refinement.source import RefinementDataSource
from automappa.pages.mag_summary.source import SummaryDataSource

from automappa.pages.home.layout import render as render_home_layout
from automappa.pages.mag_refinement.layout import render as render_mag_refinement_layout
from automappa.pages.mag_summary.layout import render as render_mag_summary_layout
from automappa.pages.not_found_404 import render as render_not_found_404

logger = logging.getLogger(__name__)


def render(
    app: DashProxy,
    storage_type: Literal["memory", "session", "local"] = "session",
    clear_data: bool = False,
) -> html.Div:
    home_data_source = HomeDataSource()
    home_page = render_home_layout(source=home_data_source)
    home_page.register(
        app=app,
        module=home_page.name,
        **dict(
            name=home_page.name,
            description=home_page.description,
            title=home_page.title,
            icon=home_page.icon,
            top_nav=True,
            order=0,
            path="/",
            redirect_from=["/home"],
        )
    )
    refinement_source = RefinementDataSource()
    mag_refinement_page = render_mag_refinement_layout(source=refinement_source)
    mag_refinement_page.register(
        app=app,
        module=mag_refinement_page.name,
        **dict(
            name=mag_refinement_page.name,
            description=mag_refinement_page.description,
            title=mag_refinement_page.title,
            icon=mag_refinement_page.icon,
            top_nav=False,
            order=1,
        )
    )
    summary_source = SummaryDataSource()
    mag_summary_page = render_mag_summary_layout(source=summary_source)
    mag_summary_page.register(
        app=app,
        module=mag_summary_page.name,
        **dict(
            name=mag_summary_page.name,
            description=mag_summary_page.description,
            title=mag_summary_page.title,
            icon=mag_summary_page.icon,
            top_nav=False,
            order=2,
        )
    )
    not_found_404_page = render_not_found_404()
    not_found_404_page.register(
        app=app,
        module=not_found_404_page.name,
    )

    # Setup main app layout.
    return dmc.MantineProvider(
        dmc.NotificationsProvider(
            dmc.Container(
                [
                    metagenome_id_store.render(app, storage_type, clear_data),
                    tasks_store.render(app, storage_type, clear_data),
                    pages_navbar.render(),
                    dash.page_container,
                ],
                fluid=True,
            )
        )
    )
