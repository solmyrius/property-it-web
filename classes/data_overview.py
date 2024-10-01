from classes.datatable import DataTable
from classes.gis_helper import GisHelper
from classes.data_schools import DataSchools


class DataOverview:
    def __init__(self):
        self.data_schools = DataSchools()

    def get_section_data(self, point):
        gis = GisHelper()

        schools = self.data_schools.get_overview_point(point)

        dt = DataTable()
        dt.put_header(['Parameter', 'Value'])

        dt.add_row([
            'Schools in 3km',
            schools['count']
        ])

        div_overview = f"""<div id="pi-schools">
            {dt.get_html()}
            </div>"""

        return {
            'result': 'success',
            'point': point,
            'title': gis.reverse_geocode(point),
            'html': div_overview
        }
