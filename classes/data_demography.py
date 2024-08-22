import json

from classes.helper import round_two_digits
from classes.gis_helper import GisHelper
from classes.pgconn import pdb_conn

"""
Quantiles:
education
[9.49, 9.72, 9.89, 10.02, 10.15, 10.3, 10.5]

institutional population:
[0.0, 0.0, 0.031, 0.174, 0.36, 0.6355, 1.136]

unoccupied dwellings:
[15.32625, 20.87, 27.22, 34.435, 42.7, 51.4375, 62.96]

homeless
[0.18, 0.31, 0.47, 0.66, 0.94, 1.4725, 2.7]

camp dwellers
no sense since only part of communes have such
[0.14625, 0.34, 0.57, 1.005, 1.6624999999999999, 2.685, 4.42875] 
"""


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
            table_key = "edu_"+key.lower()
            n = info[table_key]
            p = round(100*n/info['edu_all'], 1)
            label = self.education_rules[key]['label_it']
            label = label[0:1].upper()+label[1:]

            data_rows.append(f"""<tr>
            <td>{label}</td>
            <td>{n}</td>
            <td>{p}</td>
            </tr>""")

        return {
            "result": "success",
            "point": point,
            "title": address,
            "html": f"""<table class="pi-data-table pi-data-table-3">{''.join(data_rows)}</table>"""
        }
