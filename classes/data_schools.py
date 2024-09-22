import json
import re
import pandas as pd

from classes.helper_view import round_two_digits, signed_round, round_kmm
from classes.gis_helper import GisHelper
from classes.datatable import DataTable
from classes.pgconn import pdb_conn


class DataSchools:
    def __init__(self):
        pass

    def query_point(self, point):

        radius = 3000

        sql = f"""SELECT 
            s.*,
            ST_Distance(
                sg.point::geography,
                ST_SetSRID(ST_MakePoint(%(center_lng)s, %(center_lat)s), 4326)::geography
            ) as distance 
        FROM prop_schools_geo as sg
        LEFT JOIN prop_schools as s ON sg.school_id = s.codicescuola
        WHERE 
            ST_Distance(
                sg.point::geography,
                ST_SetSRID(ST_MakePoint(%(center_lng)s, %(center_lat)s), 4326)::geography
            ) < {radius}
        ORDER BY distance
        """

        conn = pdb_conn()
        cur = conn.cursor()
        cur.execute(sql, {'center_lng': point[0], 'center_lat': point[1]})
        rows = cur.fetchall()

        return rows

    def get_section_data(self, point):

        gis = GisHelper()
        address = gis.reverse_geocode(point)

        schools = self.query_point(point)

        dt = DataTable()
        dt.put_header([
            'Scuola',
            'Distanza'
        ])

        for row in schools[:10]:
            dt.add_row([
                row['denominazionescuola'],
                round_kmm(row['distance'])
            ])

        div_school = f"""<div id="pi-schools">
            <div>Ci sono in totale {len(schools)} scuole in un raggio di 3 km.</div>
            {dt.get_html()}
            </div>"""

        return {
            "result": "success",
            "point": point,
            "title": address,
            "html": div_school
        }
