import json

from classes.helper import round_kmm, round_two_digits
from classes.gis_helper import GisHelper
from classes.pgconn import pdb_conn


class DataAmenity:
    def __init__(self):
        with open("./classes/amenities-ruleset.json", "r") as f:
            self.amenity_types = json.load(f)
        self.conn = pdb_conn()

    def query_point(self, point):

        res = {}
        cur = self.conn.cursor()

        for amenity in self.amenity_types:

            sql = f"""
            SELECT amenity_id, amenity_type, name,
            ST_Distance(
                point::geography,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
            ) AS distance
            FROM prop_amenities
            WHERE amenity_type = %s
            ORDER BY distance
            LIMIT 10;
            """

            cur.execute(sql, (point[0], point[1], amenity))
            rows = cur.fetchall()
            for row in rows:
                row['distance_formatted'] = round_kmm(row['distance'])
            res[amenity] = rows

        cur.close()

        return res

    def get_section_data(self, point):

        gis = GisHelper()
        address = gis.reverse_geocode(point)

        info = self.query_point(point)
        amt_parts = []
        for amenity in info:
            amt_rows = []
            for row in info[amenity]:
                amt_rows.append(f"<tr><td>{row['name']}</td><td>{row['distance_formatted']}</td></tr>")
            amt_parts.append(f"""<table id="pi-amenity-table-{amenity}">{''.join(amt_rows)}</table>""")

        return {
            "result": "success",
            "point": point,
            "title": address,
            "html": ''.join(amt_parts)
        }

    def get_overview(self, point):
        radius = 3000  # meters
        res = {}
        cur = self.conn.cursor()

        sql = f"""
            SELECT COUNT(*) as cnt, amenity_type
            FROM prop_amenities
            WHERE ST_Distance(
                point::geography,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
            ) < %s
            GROUP BY (amenity_type)
            """

        cur.execute(sql, (point[0], point[1], radius))
        rows = cur.fetchall()
        cur.close()

        res['amenity_counts'] = {}
        for row in rows:
            res['amenity_counts'][row['amenity_type']] = row['cnt']

        return res

    def get_compare(self, point):
        res = {}

        """ Overview data is used for counting amenities within radius. The same radius as for overview is used """
        res_overview = self.get_overview(point)

        total = 0
        for tp in res_overview['amenity_counts']:
            res['count_'+tp] = f"{res_overview['amenity_counts'][tp]}"
            total += res_overview['amenity_counts'][tp]

        res['count_total'] = f"{total}"

        proximity_radius = 20000

        cur = self.conn.cursor()

        def_labels = self.get_labels()

        sql = f"""
            WITH RankedPoints AS (
            SELECT
                name,
                amenity_type,
                ST_Distance(
                    point::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) as distance,
                ROW_NUMBER() OVER (PARTITION BY amenity_type ORDER BY ST_Distance(point, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) ASC) as rn
            FROM
                amenities
            WHERE ST_Distance(
                    point::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) < %s
            )
        SELECT
            name,
            amenity_type,
            distance
        FROM
            RankedPoints
        WHERE
            rn = 1;
        """
        cur.execute(sql, (point[0], point[1], point[0], point[1], point[0], point[1], proximity_radius))
        rows = cur.fetchall()
        cur.close()
        closest = {}
        for row in rows:
            closest[row['amenity_type']] = row

        for tp in def_labels:
            name = def_labels[tp]['label']
            if tp in closest and closest[tp]['name'] is not None:
                name = closest[tp]['name']
            if tp in closest:
                res[tp] = f"{name} <br/> ({round_kmm(closest[tp]['distance'])})"
            else:
                res[tp] = '-'

            if 'count_'+tp not in res:
                res['count_'+tp] = "0"

        return res

    @staticmethod
    def get_labels():
        return {
            'supermarket': {
                'label': 'Supermarket',
            },
            'store': {
                'label': 'Convenience store',
            },
            'restaurant': {
                'label': 'Restaurant',
            },
            'cafe': {
                'label': 'Cafe',
            },
            'medical': {
                'label': 'Hospital',
            },
            'pub': {
                'label': 'Pub',
            },
            'park': {
                'label': 'Park',
            },
            'sport': {
                'label': 'Fitness',
            },
        }

    def get_widget(self, point):

        res = {
            'supermarket': [],
            'restaurant': [],
            'pub': [],
            'medical': []
        }
        cur = self.conn.cursor()

        def_labels = self.get_labels()

        for amenity in ['supermarket', 'restaurant', 'pub', 'medical']:

            sql = f"""
            SELECT amenity_id, amenity_type, name,
            ST_Distance(
                point::geography,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
            ) AS distance
            FROM amenities
            WHERE amenity_type = %s
            ORDER BY distance
            LIMIT 3;
            """

            cur.execute(sql, (point[0], point[1], amenity))
            rows = cur.fetchall()
            for row in rows:
                row['distance_formatted'] = round_kmm(row['distance'])
                if row['name'] is None:
                    row['name'] = def_labels[amenity]['label']
                res[amenity].append(self.format_widget_row(row))

        return res

    @staticmethod
    def format_widget_row(row):
        return f"""<tr>
                    <td>
                        {row['name']}
                    </td>
                    <td>
                        {row['distance_formatted']}
                    </td>
                    <td></td>
                </tr>"""
