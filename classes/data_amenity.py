import json

from classes.helper import round_kmm, round_two_digits
from classes.gis_helper import GisHelper
from classes.pgconn import pdb_conn


class DataAmenity:
    def __init__(self):
        with open("./classes/amenities-ruleset.json", "r") as f:
            self.amenity_types = json.load(f)
        self.conn = pdb_conn()

    def get_buttons(self):
        buttons = [self.make_button('all')]
        for amt in self.amenity_types:
            if amt != 'all':
                buttons.append(self.make_button(amt))
        return buttons

    def make_button(self, amt):
        return {
            'amenity': amt,
            'label': self.amenity_types[amt]['label'],
            'icon': self.amenity_types[amt]['icon'],
        }

    def query_point(self, point):

        res = {
            'counts': {},
            'rows': []
        }
        cur = self.conn.cursor()
        half_side = 3000  # meters

        sql = f"""
            SELECT amenity_id, amenity_type, name,
            ST_Distance(
                point::geography,
                ST_SetSRID(ST_MakePoint(%(center_lng)s, %(center_lat)s), 4326)::geography
            ) AS distance
            FROM
            
            (SELECT *
            FROM prop_amenities
            WHERE ST_Contains(
                ST_Transform(
                    ST_SetSRID(
                        ST_MakeEnvelope(
                            %(center_lng)s - %(half_side)s * cos(radians(%(center_lat)s)) / 111319.9,
                            %(center_lat)s - %(half_side)s / 111319.9,
                            %(center_lng)s + %(half_side)s * cos(radians(%(center_lat)s)) / 111319.9,
                            %(center_lat)s + %(half_side)s / 111319.9,
                            4326
                        ),
                    4326),
                4326),
                point
            )) as pre_fetch
            ORDER BY distance;
        """
        cur.execute(sql, {'center_lng': point[0], 'center_lat': point[1], 'half_side': half_side})
        rows = cur.fetchall()
        cur.close()

        for row in rows:
            row['distance_formatted'] = round_kmm(row['distance'])
            res['rows'].append(row)
            if row['amenity_type'] in res['counts']:
                res['counts'][row['amenity_type']] += 1
            else:
                res['counts'][row['amenity_type']] = 1

        return res

    def get_section_data(self, point):

        gis = GisHelper()
        address = gis.reverse_geocode(point)

        info = self.query_point(point)
        amt_rows = []
        for row in info['rows']:
            amt_icon = f"/static/images/amenities/{self.amenity_types[row['amenity_type']]['icon']}"
            amt_name = row['name']
            if amt_name is None:
                amt_name = self.amenity_types[row['amenity_type']]['label']
            amt_rows.append(f"""
                <tr data-distance="{row['distance']}" data-amenity="{row['amenity_type']}">
                    <td>
                        <div class="pi-a-row">
                            <span class="pi-a-row-icon">
                                <img src="{amt_icon}" alt="Icon {amt_name}" />
                            </span>
                            <span class="pi-a-row-label">{amt_name}</span>
                        </div>
                    </td>
                    <td>
                        {row['distance_formatted']}
                    </td>
                </tr>""")

        return {
            "result": "success",
            "point": point,
            "title": address,
            "html": f"""<table id="pi-amenity-table" class="pi-data-table pi-data-table-2">{''.join(amt_rows)}</table>"""
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
