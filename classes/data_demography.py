import json
import re

from classes.helper import round_two_digits, signed_round
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


class DemographyTable:
    def __init__(self):
        self.columns = 3
        self.row_header = []
        self.rows_body = []

    def put_header(self, row):
        self.row_header = row

    def add_row(self, row, style=None):

        cells = []
        for idx, item in enumerate(row):
            cls = "pi-dt-number"
            if idx == 0:
                cls = "pi-dt-label"
            if style is not None and len(style) > idx:
                cls = style[idx]
            cells.append(f'<td class="{cls}">{item}</td>')

        self.rows_body.append(f"<tr>{''.join(cells)}</tr>")

    def get_html(self):
        header = f"""<tr><th>{'</th><th>'.join(self.row_header)}</th></tr>"""

        return f"""<table class="pi-data-table pi-data-table-{self.columns}">{header}{''.join(self.rows_body)}</table>"""


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
                csc.camp_total, csc.camp_idx,
                cage.*,
                calien.*
            FROM prop_census_commune cs
            LEFT JOIN prop_census_commune_edu cse ON cs.commune_id = cse.commune_id
            LEFT JOIN prop_census_commune_dwell csd ON cs.commune_id = csd.commune_id
            LEFT JOIN prop_census_commune_hless cshl ON cs.commune_id = cshl.commune_id
            LEFT JOIN prop_census_commune_hh cshh ON cs.commune_id = cshh.commune_id
            LEFT JOIN prop_census_commune_camp csc ON cs.commune_id = csc.commune_id
            LEFT JOIN prop_population_age cage ON cs.commune_id = cage.commune_id
            LEFT JOIN prop_population_alien calien ON cs.commune_id = calien.commune_id
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
                cs.commune_id, cs.name,
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
            ig.commune_id, ig.name,
            cse.*,
            csd.dwell_total, csd.dwell_idx,
            cshl.hless_total, cshl.hless_idx,
            cshh.hh_respop, cshh.hh_inst_respop, cshh.hh_avg_dw, cshh.hh_idx,
            csc.camp_total, csc.camp_idx,
            cage.*,
            calien.*,
            bb.joint_bbox
        FROM IntersectedGeoms ig
        LEFT JOIN prop_census_commune_edu cse ON ig.commune_id = cse.commune_id
        LEFT JOIN prop_census_commune_dwell csd ON ig.commune_id = csd.commune_id
        LEFT JOIN prop_census_commune_hless cshl ON ig.commune_id = cshl.commune_id
        LEFT JOIN prop_census_commune_hh cshh ON ig.commune_id = cshh.commune_id
        LEFT JOIN prop_census_commune_camp csc ON ig.commune_id = csc.commune_id
        LEFT JOIN prop_population_age cage ON ig.commune_id = cage.commune_id
        LEFT JOIN prop_population_alien calien ON ig.commune_id = calien.commune_id        
        CROSS JOIN BoundingBox bb;
        """
        cur = self.conn.cursor()
        cur.execute(sql, (point[0], point[1]))
        rows = cur.fetchall()

        res = []
        for row in rows:
            res.append({k: (v if v is not None else 0) for k, v in row.items()})

        return res

    def query_aliens(self, commune_id, communes):
        aliens = {}
        sql = f"SELECT * FROM prop_population_alien_country WHERE commune_id = ANY(%s)"
        cur = self.conn.cursor()
        cur.execute(sql, ([commune_id] + communes, ))
        rows = cur.fetchall()
        for row in rows:
            if row['zone_name'] not in ['Unione Europea', 'Altri paesi europei']:
                if row['country_code'] not in aliens:
                    aliens[row['country_code']] = {
                        'info': row,
                        'commune': 0,
                        'nearby': 0
                    }
                if row['commune_id'] == commune_id:
                    aliens[row['country_code']]['commune'] = row['population_t']
                else:
                    aliens[row['country_code']]['nearby'] += row['population_t']
        return dict(sorted(aliens.items(), key=lambda item: item[1]['commune'], reverse=True))

    def get_section_data(self, point):

        gis = GisHelper()
        address = gis.reverse_geocode(point)

        info = self.query_point(point)
        commune_id = info["commune_id"]

        """ Nearby communes """

        nearby_info = self.query_nearby(point)

        nearby_ids = []
        nearby_frags = []
        for row in nearby_info:
            nearby_ids.append(row['commune_id'])
            nearby_frags.append(f"<span>{row['name']}</span>")

        nearby_note_html = f"""<div class="pi-data-table-note">
        * Comuni limitrofi: {', '.join(nearby_frags)}
        </div>"""

        """ Eduction """

        edu_keys = ['IL', 'LBNA', 'PSE', 'LSE', 'USE_IF', 'BL', 'ML', 'RDD']

        nearby_edu = self.nearby_average(
            nearby_info,
            ['edu_'+x.lower() for x in edu_keys]+['edu_idx'],
            'edu_all'
        )

        print(info, flush=True)

        data_rows = [
            f"""<tr><th>Istruzione</th><th>Comune selezionato {info['name']}</th><th>Comuni limitrofi</th></tr>""",
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

        div_edu = f"""<div id="pi-demography-education" class="pi-ss-pane">
            <table class="pi-data-table pi-data-table-3">{''.join(data_rows)}</table>
            </div>"""

        """ Unoccupied dwellings """

        nearby_dwell = self.nearby_average(nearby_info, ['dwell_idx'], 'dwell_total')
        data_rows = [
            f"""<tr><th>Dwellings</th><th>Comune selezionato {info['name']}</th><th>Comuni limitrofi</th></tr>""",
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

        div_dwell = f"""<div id="pi-demography-unoccupied" class="pi-ss-pane">
            <table class="pi-data-table pi-data-table-3">{''.join(data_rows)}</table>
            </div>"""

        """ Homeless """
        nearby_populi = self.nearby_average(nearby_info, ['hless_idx', 'hless_total', 'camp_idx', 'camp_total', 'hh_idx', 'hh_inst_respop', 'hh_avg_dw'], 'hh_respop')

        data_rows = [
            f"""<tr><th>Homeless</th><th>Comune selezionato {info['name']}</th><th>Comuni limitrofi</th></tr>""",
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

        div_homeless = f"""<div id="pi-demography-homeless" class="pi-ss-pane">
            <table class="pi-data-table pi-data-table-3">{''.join(data_rows)}</table>
            </div>"""

        """ Camps """

        data_rows = [
            f"""<tr><th>Camps dwellers</th><th>Comune selezionato {info['name']}</th><th>Comuni limitrofi</th></tr>""",
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

        div_camp = f"""<div id="pi-demography-camp" class="pi-ss-pane">
            <table class="pi-data-table pi-data-table-3">{''.join(data_rows)}</table>
            </div>"""

        """ Institutional """

        data_rows = [
            f"""<tr><th>Institutional dwellings</th><th>Comune selezionato {info['name']}</th><th>Comuni limitrofi</th></tr>""",
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

        div_inst = f"""<div id="pi-demography-institutional" class="pi-ss-pane">
            <table class="pi-data-table pi-data-table-3">{''.join(data_rows)}</table>
            </div>"""

        """ Age """
        nearby_age = self.nearby_average(
            nearby_info,
            ['median_age', 'median_age_m', 'median_age_f', 'median_age_change', 'age_population_change'],
            'age_population'
        )

        median_age_change = f"{info['median_age_change']:.1f}"
        if info['median_age_change'] > 0:
            median_age_change = '+'+median_age_change

        median_age_change_nearby = f"{nearby_age['weighted']['median_age_change']:.1f}"
        if nearby_age['weighted']['median_age_change'] > 0:
            median_age_change_nearby = '+'+median_age_change_nearby

        age_rows = [
            f"""<tr><th>Parametro di età</th><th>Comune selezionato {info['name']}</th><th>Comuni limitrofi</th></tr>""",
            f"""<tr>
                <td class="pi-dt-label">Età mediana</td>           
                <td class="pi-dt-number">{info['median_age']:.1f} anni</td>
                <td class="pi-dt-number">{nearby_age['weighted']['median_age']:.1f} anni</td>
            </tr>""",
            f"""<tr>
                <td class="pi-dt-label">Età mediana maschi</td>           
                <td class="pi-dt-number">{info['median_age_m']:.1f} anni</td>
                <td class="pi-dt-number">{nearby_age['weighted']['median_age_f']:.1f} anni</td>
            </tr>""",
            f"""<tr>
                <td class="pi-dt-label">Età mediana femmine</td>           
                <td class="pi-dt-number">{info['median_age_f']:.1f} anni</td>
                <td class="pi-dt-number">{nearby_age['weighted']['median_age_f']:.1f} anni</td>
            </tr>""",
            f"""<tr>
                <td class="pi-dt-label">Variazione dell'età mediana</td>           
                <td class="pi-dt-number">{median_age_change} anni</td>
                <td class="pi-dt-number">{median_age_change_nearby} anni</td>
            </tr>""",
            f"""<tr>
                <td class="pi-dt-label">Variazione della popolazione</td>           
                <td class="pi-dt-number">{info['age_population_change']} ({info['age_population']})</td>
                <td class="pi-dt-number">{nearby_age['sum']['age_population_change']} ({nearby_age['total']})</td>
            </tr>""",
        ]

        div_age = f"""<div id="pi-demography-age" class="pi-ss-pane">
            <table class="pi-data-table pi-data-table-3">{''.join(age_rows)}</table>
            </div>"""

        """ Aliens """
        nearby_alien = self.nearby_average(
            nearby_info,
            ['alien_population_noneu', 'alien_idx', 'alien_idx_change'],
            'alien_population_total'
        )

        countries = self.query_aliens(commune_id, nearby_ids)

        dt = DemographyTable()
        dt.put_header([
            "Parametro Forestieri", f"Comune selezionato {info['name']}", "Comuni limitrofi<sup>*</sup>"
        ])
        dt.add_row([
            "Indice degli forestieri",
            f"{info['alien_idx']:.1f}",
            f"{nearby_alien['weighted']['alien_idx']:.1f}"
        ])
        dt.add_row([
            f"Variazione Indice degli forestieri ({info['alien_base_year']}-{info['alien_last_year']})",
            signed_round(info['alien_idx_change'], 1),
            signed_round(nearby_alien['weighted']['alien_idx_change'], 1)
        ])
        dt.add_row([
            f"Numero di residenti nati fuori dall'UE",
            info['alien_population_noneu'],
            nearby_alien['sum']['alien_population_noneu']
        ])

        for country in countries.values():
            dt.add_row([
                country['info']['country_name'],
                country['commune'],
                country['nearby']
            ])

        div_alien = f"""<div id="pi-demography-alien" class="pi-ss-pane">
            <div>I dati demografici sugli stranieri sono riferiti al {info['alien_last_year']}</div>
            {dt.get_html()}
            </div>"""

        """ Combined """

        data_rows = [
            f"""<tr><th>Demography index</th><th>Comune selezionato {info['name']}</th><th>Comuni limitrofi</th></tr>""",
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

        div_combined = f"""<div id="pi-demography-combined" class="pi-ss-pane">
            <table class="pi-data-table pi-data-table-3">{''.join(data_rows)}</table>
            </div>"""

        return {
            "result": "success",
            "point": point,
            "selected": info['commune_id'],
            "nearby": nearby_ids,
            "bbox": self.polygon_to_bounds(nearby_info[0]['joint_bbox']),
            "title": address,
            "countries": countries,
            "html": div_combined+div_edu+div_dwell+div_homeless+div_camp+div_inst+div_age+div_alien+nearby_note_html
        }
