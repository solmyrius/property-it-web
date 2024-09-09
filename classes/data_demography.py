import json
import re

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

        sql = f"""
            SELECT
                cs.commune_id as commune_id,
                cs.name as name,
                cse.*,
                csd.dwell_total, csd.dwell_idx,
                cshl.hless_total, cshl.hless_idx,
                cshh.hh_respop, cshh.hh_inst_respop, cshh.hh_avg_dw, cshh.hh_idx,
                csc.camp_total, csc.camp_idx
            FROM prop_census_commune cs
            LEFT JOIN prop_census_commune_edu cse ON cs.commune_id = cse.commune_id
            LEFT JOIN prop_census_commune_dwell csd ON cs.commune_id = csd.commune_id
            LEFT JOIN prop_census_commune_hless cshl ON cs.commune_id = cshl.commune_id
            LEFT JOIN prop_census_commune_hh cshh ON cs.commune_id = cshh.commune_id
            LEFT JOIN prop_census_commune_camp csc ON cs.commune_id = csc.commune_id
            WHERE ST_Intersects(
                cs.geom,
                ST_SetSRID(ST_Point(%s, %s), 4326)
            )
        """
        cur = self.conn.cursor()
        cur.execute(sql, (point[0], point[1]))
        row = cur.fetchone()
        cur.close()

        row = {k: (v if v is not None else 0) for k, v in row.items()}

        return row

    @staticmethod
    def polygon_to_bounds(polygon_string):
        coords_text = re.findall(r'\(\((.+?)\)\)', polygon_string)[0]
        coords_pairs = coords_text.split(',')

        # Converting string coordinates to tuples of floats (longitude, latitude)
        coords = [tuple(map(float, coord.split())) for coord in coords_pairs]

        # Extracting the min and max longitude and latitude
        min_lon = min(coords, key=lambda x: x[0])[0]
        max_lon = max(coords, key=lambda x: x[0])[0]
        min_lat = min(coords, key=lambda x: x[1])[1]
        max_lat = max(coords, key=lambda x: x[1])[1]

        # Returning the bounds in the format [[west, south], [east, north]]
        return [[min_lon, min_lat], [max_lon, max_lat]]

    @staticmethod
    def nearby_average(nearby_info, param_keys, total_key):
        param_total = {key: 0 for key in param_keys}
        param_weighted = {key: 0 for key in param_keys}
        total = 0
        for row in nearby_info:
            total = total + row[total_key]
            for key in param_keys:
                param_total[key] = param_total[key] + row[key]
                param_weighted[key] = param_weighted[key] + row[total_key] * row[key]

        print('param_total', flush=True)
        print(param_total, flush=True)
        print('param_weighted', flush=True)
        print(param_weighted, flush=True)

        return {
            'total': total,
            'sum': {key: param_total[key] for key in param_total},
            'average': {key: param_total[key] / total for key in param_total},
            'weighted': {key: param_weighted[key] / total for key in param_weighted}
        }

    def query_nearby(self, point):

        sql = f"""
        WITH SelectedShape AS (
            SELECT commune_id, ST_Buffer(geom, 0.0001) AS buffered_geom
            FROM prop_census_commune
            WHERE ST_Contains(geom, ST_SetSRID(ST_Point(%s, %s), 4326))
        ),
        IntersectedGeoms AS (
            SELECT 
                cs.commune_id, 
                cs.geom
            FROM prop_census_commune cs
            INNER JOIN SelectedShape ss ON ST_Intersects(cs.geom, ss.buffered_geom)
            WHERE cs.commune_id != ss.commune_id
        ),
        BoundingBox AS (
            SELECT ST_AsText(ST_Envelope(ST_Collect(geom))) AS joint_bbox
            FROM IntersectedGeoms
        )
        SELECT 
            ig.commune_id, 
            cse.*,
            csd.dwell_total, csd.dwell_idx,
            cshl.hless_total, cshl.hless_idx,
            cshh.hh_respop, cshh.hh_inst_respop, cshh.hh_avg_dw, cshh.hh_idx,
            csc.camp_total, csc.camp_idx,
            bb.joint_bbox
        FROM IntersectedGeoms ig
        LEFT JOIN prop_census_commune_edu cse ON ig.commune_id = cse.commune_id
        LEFT JOIN prop_census_commune_dwell csd ON ig.commune_id = csd.commune_id
        LEFT JOIN prop_census_commune_hless cshl ON ig.commune_id = cshl.commune_id
        LEFT JOIN prop_census_commune_hh cshh ON ig.commune_id = cshh.commune_id
        LEFT JOIN prop_census_commune_camp csc ON ig.commune_id = csc.commune_id
        CROSS JOIN BoundingBox bb;
        """
        cur = self.conn.cursor()
        cur.execute(sql, (point[0], point[1]))
        rows = cur.fetchall()

        res = []
        for row in rows:
            res.append({k: (v if v is not None else 0) for k, v in row.items()})

        return res

    def get_section_data(self, point):

        gis = GisHelper()
        address = gis.reverse_geocode(point)

        info = self.query_point(point)
        nearby_info = self.query_nearby(point)

        """ Eduction """

        edu_keys = ['IL', 'LBNA', 'PSE', 'LSE', 'USE_IF', 'BL', 'ML', 'RDD']

        nearby_edu = self.nearby_average(
            nearby_info,
            ['edu_'+x.lower() for x in edu_keys]+['edu_idx'],
            'edu_all'
        )

        print(info, flush=True)

        data_rows = [
            f"""<tr><th>Education</th><th>Selected region</th><th>Nearby regions</th></tr>""",
            f"""<tr>
                <td class="pi-dt-label">Overall Education Index</td>           
                <td class="pi-dt-number">{info['edu_idx']}</td>
                <td class="pi-dt-number">{round(nearby_edu['weighted']['edu_idx'], 1)}</td>
            </tr>"""
        ]
        for key in ['IL', 'LBNA', 'PSE', 'LSE', 'USE_IF', 'BL', 'ML', 'RDD']:
            table_key = "edu_"+key.lower()
            n = info[table_key]
            p = round(100*n/info['edu_all'], 1)
            label = self.education_rules[key]['label_it']
            label = label[0:1].upper()+label[1:]

            data_rows.append(f"""<tr>
            <td class="pi-dt-label">{label}</td>
            <td class="pi-dt-number">{p}%</td>
            <td class="pi-dt-number">{round(100*nearby_edu['average'][table_key], 1)}%</td>
            </tr>""")

        table_edu = f"""<table id="pi-demography-education" class="pi-data-table pi-data-table-3">{''.join(data_rows)}</table>"""

        """ Unoccupied dwellings """

        nearby_dwell = self.nearby_average(nearby_info, ['dwell_idx'], 'dwell_total')
        data_rows = [
            f"""<tr><th>Dwellings</th><th>Selected region</th><th>Nearby regions</th></tr>""",
            f"""<tr>
                <td class="pi-dt-label">Unoccupied dwellings index</td>           
                <td class="pi-dt-number">{info['dwell_idx']}%</td>
                <td class="pi-dt-number">{round(nearby_dwell['weighted']['dwell_idx'], 1)}%</td>
            </tr>""",
            f"""<tr>
                <td class="pi-dt-label">Total number of dwellings</td>           
                <td class="pi-dt-number">{info['dwell_total']}</td>
                <td class="pi-dt-number">{nearby_dwell['total']}</td>
            </tr>""",
        ]

        table_dwell = f"""<table id="pi-demography-unoccupied" class="pi-data-table pi-data-table-3">{''.join(data_rows)}</table>"""

        """ Homeless """
        nearby_populi = self.nearby_average(nearby_info, ['hless_idx', 'hless_total', 'camp_idx', 'camp_total', 'hh_idx', 'hh_inst_respop', 'hh_avg_dw'], 'hh_respop')

        data_rows = [
            f"""<tr><th>Homeless</th><th>Selected region</th><th>Nearby regions</th></tr>""",
            f"""<tr>
                <td class="pi-dt-label">Homeless index</td>           
                <td class="pi-dt-number">{info['hless_idx']}%</td>
                <td class="pi-dt-number">{round(nearby_populi['weighted']['hless_idx'], 1)}%</td>
            </tr>""",
            f"""<tr>
                <td class="pi-dt-label">Total number of homeless</td>           
                <td class="pi-dt-number">{info['hless_total']}</td>
                <td class="pi-dt-number">{nearby_populi['sum']['hless_total']}</td>
            </tr>""",
        ]

        table_homeless = f"""<table id="pi-demography-homeless" class="pi-data-table pi-data-table-3">{''.join(data_rows)}</table>"""

        """ Camps """

        data_rows = [
            f"""<tr><th>Camps dwellers</th><th>Selected region</th><th>Nearby regions</th></tr>""",
            f"""<tr>
                <td class="pi-dt-label">Camp dweller index</td>           
                <td class="pi-dt-number">{info['camp_idx']}%</td>
                <td class="pi-dt-number">{round(nearby_populi['weighted']['camp_idx'], 1)}%</td>
            </tr>""",
            f"""<tr>
                <td class="pi-dt-label">Total number of camp dwellers</td>           
                <td class="pi-dt-number">{info['camp_total']}</td>
                <td class="pi-dt-number">{nearby_populi['sum']['camp_total']}</td>
            </tr>""",
        ]

        table_camp = f"""<table id="pi-demography-camp" class="pi-data-table pi-data-table-3">{''.join(data_rows)}</table>"""

        """ Institutional """

        data_rows = [
            f"""<tr><th>Institutional dwellings</th><th>Selected region</th><th>Nearby regions</th></tr>""",
            f"""<tr>
                <td class="pi-dt-label">Institutional dweller index</td>           
                <td class="pi-dt-number">{info['hh_idx']}%</td>
                <td class="pi-dt-number">{round(nearby_populi['weighted']['hh_idx'], 1)}%</td>
            </tr>""",
            f"""<tr>
                <td class="pi-dt-label">Total number of institutional dwellers</td>           
                <td class="pi-dt-number">{info['hh_inst_respop']}</td>
                <td class="pi-dt-number">{nearby_populi['sum']['hh_inst_respop']}</td>
            </tr>""",
            f"""<tr>
                <td class="pi-dt-label">Average family members in household</td>           
                <td class="pi-dt-number">{info['hh_avg_dw']}</td>
                <td class="pi-dt-number">{round(nearby_populi['weighted']['hh_avg_dw'],1)}</td>
            </tr>"""
        ]

        table_inst = f"""<table id="pi-demography-institutional" class="pi-data-table pi-data-table-3">{''.join(data_rows)}</table>"""

        """ Age """

        """ Combined """

        data_rows = [
            f"""<tr><th>Demography index</th><th>Selected region</th><th>Nearby regions</th></tr>""",
            f"""<tr>
                <td class="pi-dt-label">Education Index</td>           
                <td class="pi-dt-number">{info['edu_idx']}</td>
                <td class="pi-dt-number">{round(nearby_edu['weighted']['edu_idx'], 1)}</td>
            </tr>""",
            f"""<tr>
                <td class="pi-dt-label">Unoccupied dwellings index</td>           
                <td class="pi-dt-number">{info['dwell_idx']}%</td>
                <td class="pi-dt-number">{round(nearby_dwell['weighted']['dwell_idx'], 1)}%</td>
            </tr>""",
            f"""<tr>
                <td class="pi-dt-label">Homeless index</td>           
                <td class="pi-dt-number">{info['hless_idx']}%</td>
                <td class="pi-dt-number">{round(nearby_populi['weighted']['hless_idx'], 1)}%</td>
            </tr>""",
            f"""<tr>
                <td class="pi-dt-label">Camp dweller index</td>           
                <td class="pi-dt-number">{info['camp_idx']}%</td>
                <td class="pi-dt-number">{round(nearby_populi['weighted']['camp_idx'], 1)}%</td>
            </tr>""",
            f"""<tr>
                <td class="pi-dt-label">Institutional dweller index</td>           
                <td class="pi-dt-number">{info['hh_idx']}%</td>
                <td class="pi-dt-number">{round(nearby_populi['weighted']['hh_idx'], 1)}%</td>
            </tr>""",
        ]

        table_combined = f"""<table id="pi-demography-combined" class="pi-data-table pi-data-table-3">{''.join(data_rows)}</table>"""

        """ Nearby communes """

        nearby_ids = []
        for row in nearby_info:
            nearby_ids.append(row['commune_id'])

        return {
            "result": "success",
            "point": point,
            "selected": info['commune_id'],
            "nearby": nearby_ids,
            "bbox": self.polygon_to_bounds(nearby_info[0]['joint_bbox']),
            "title": address,
            "html": table_combined+table_edu+table_dwell+table_homeless+table_camp+table_inst
        }
