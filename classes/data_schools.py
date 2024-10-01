import json
import re
import pandas as pd

from classes.helper_view import round_two_digits, signed_round, round_kmm
from classes.gis_helper import GisHelper
from classes.datatable import DataTable
from classes.pgconn import pdb_conn


class DataSchools:
    def __init__(self):
        self.radius = 3000

    def query_point(self, point):

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
            ) < {self.radius}
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
                f"""<a href="/scuola/{row['codicescuola']}">{row['denominazionescuola']}</a>""",
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

    def get_overview_point(self, point):
        sql = f"""SELECT count(*) as cnt
        FROM prop_schools_geo as sg
        WHERE 
            ST_Distance(
                sg.point::geography,
                ST_SetSRID(ST_MakePoint(%(center_lng)s, %(center_lat)s), 4326)::geography
            ) < {self.radius}"""

        conn = pdb_conn()
        cur = conn.cursor()
        cur.execute(sql, {'center_lng': point[0], 'center_lat': point[1]})
        row = cur.fetchone()

        return {
            'count': row['cnt'],
        }

    def get_school_data(self, school_id):
        sql = f"""SELECT * FROM prop_schools
            WHERE codicescuola = %(school_id)s"""

        conn = pdb_conn()
        cur = conn.cursor()
        cur.execute(sql, {'school_id': school_id})
        school = cur.fetchone()

        dt = DataTable()
        dt.add_row([
            "Indirizzo della scuola",
            school['indirizzoscuola']
        ])
        dt.add_row([
            "Dell'istituto di riferimento della scuola",
            school['denominazioneistitutoriferimento']
        ])
        dt.add_row([
            "Descrizione della tipologia o del grado di istruzione della scuola",
            school['descrizionetipologiagradoistruzionescuola']
        ])
        dt.add_row([
            "Regione",
            school['regione']
        ])
        dt.add_row([
            "Provincia",
            school['provincia']
        ])
        dt.add_row([
            "Comune",
            school['descrizionecomune']
        ])
        if school['is_state'] == 'state':
            state_txt = 'Pubblico'
        else:
            state_txt = 'Privato'
        dt.add_row([
            "Pubblico/privato",
            state_txt
        ])
        dt.add_row([
            "Posta Elettronica Certificata",
            school['indirizzopecscuola']
        ])
        dt.add_row([
            "Indirizzo di posta elettronica della scuola",
            school['indirizzoemailscuola']
        ])
        if school['sitowebscuola'].lower() == 'non disponibile':
            school_web = 'Non Disponibile'
        else:
            school_web = self.format_school_web(school['sitowebscuola'])
        dt.add_row([
            "Indirizzo del sito web della scuola",
            school_web
        ])

        div_school = f"""<div id="pi-school-item">
            {dt.get_html()}
            </div>"""

        return {
            'school': school,
            'html': div_school
        }

    @staticmethod
    def format_school_web(school_web):
        if school_web[0:6] == 'http//':
            school_web = school_web[7:]
        if school_web[0:7] == 'https//':
            school_web = school_web[8:]
        if school_web[0:7] == 'http://':
            school_web = school_web[8:]

        if school_web[0:8] != 'https://':
            school_web = 'https://'+school_web

        return f'<a href="{school_web}" target=_blank>{school_web}</a>'
