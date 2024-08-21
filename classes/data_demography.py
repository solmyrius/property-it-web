import json

from classes.helper import round_two_digits
from classes.gis_helper import GisHelper
from classes.pgconn import pdb_conn


class DataDemography:
    def __init__(self):
        with open("./rules/education_rules.json", "r") as f:
            self.education_rules = json.load(f)
        self.conn = pdb_conn()

    def query_point(self, point):

        cur = self.conn.cursor()
        sql = f"""
            SELECT
                cs.commune_id as commune_id,
                cs.name as name,
                cse.*
            FROM prop_census_commune cs
            JOIN prop_census_commune_edu cse ON cs.commune_id = cse.commune_id
            WHERE ST_Intersects(
                cs.geom,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)
            )
        """
        cur.execute(sql, (point[0], point[1]))
        row = cur.fetchone()
        cur.close()

        return row

    def get_section_data(self, point):

        gis = GisHelper()
        address = gis.reverse_geocode(point)

        info = self.query_point(point)
        data_rows = [f"""<tr><th>Education</th><th>Peoples</th><th>%</th></tr>"""]
        for key in ['IL', 'LBNA', 'PSE', 'LSE', 'USE_IF', 'BL', 'ML', 'RDD']:
            data_rows.append(f"""<tr>
            <td></td>
            <td></td>
            <td></td>
            </tr>""")

        return {
            "result": "success",
            "point": point,
            "title": address,
            "html": f"""<table class="pi-data-table pi-data-table-3">{''.join(data_rows)}</table>"""
        }
