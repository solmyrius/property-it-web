import json
import re
import pandas as pd

from classes.helper_view import round_two_digits, signed_round, round_kmm
from classes.gis_helper import GisHelper
from classes.datatable import DataTable
from classes.pgconn import pdb_conn


class DataOmi:
    """
    Data from Osservatorio del Mercato Immobiliare
    Agenzia Entrante

    Sell [533.4375, 670.0, 800.0, 925.0, 1080.0, 1300.0, 1700.0]
    Rent [1.95, 2.5, 3.0, 3.5, 4.05, 4.9, 6.35]
    ROI [221.80451127819546, 243.37349397590359, 259.8425196850394, 275.7464349376114, 293.6507936507936, 308.75286041189935, 343.4343434343434]
    """
    def __init__(self):
        self.radius = 3000

    def query_point(self, point):

        sql = f"""
            SELECT
                os.commune_id as commune_id,
                os.tip_cod as prev_tip_cod,
                op.*
            FROM prop_omi_shapes os
            LEFT JOIN prop_omi_prices op ON os.link_zona = op.linkzona
            WHERE ST_Intersects(
                os.geom,
                ST_SetSRID(ST_Point(%s, %s), 4326)
            )
        """
        conn = pdb_conn()
        cur = conn.cursor()
        cur.execute(sql, (point[0], point[1]))
        rows = cur.fetchall()

        return rows

    def get_section_data(self, point):

        gis = GisHelper()
        address = gis.reverse_geocode(point)

        prices = self.query_point(point)

        last_year = 2023
        last_semester = 2

        dt = DataTable()
        dt.put_header([
            'Tipo di immobile',
            'Prezzo di vendita',
            'Costo di locazione',
            'Ritorno sugli investimenti'
        ])

        prop_types = [20, 1]  # Property types for which we are collecting data (order is important)
        chart_price_types = {}

        for row in prices:

            if row['year'] is None:
                continue  # It may happen if no data for selected commune, because LEFT JOIN is used in SQL

            if row['stato'] is None:
                property_state = ''
            else:
                property_state = f" ({row['stato'].lower()})"
            property_type = f"{row['descr_tipologia']}{property_state}"
            if row['compr_min'] is not None and row['compr_max'] is not None:
                price_sell = (float(row['compr_min'])+float(row['compr_max'])) / 2
            else:
                price_sell = None

            if row['loc_min'] is not None and row['loc_max'] is not None:
                price_rent = (float(row['loc_min'])+float(row['loc_max'])) / 2
            else:
                price_rent = None

            roi = None
            if price_sell is not None and price_rent is not None and price_rent!=0:
                roi = price_sell/price_rent

            # Collecting live table data
            if row['year'] == last_year and row['semester'] == last_semester:

                type_row = [property_type]
                if price_sell is not None:
                    type_row.append(f"{price_sell:.0f}€")
                else:
                    type_row.append('')

                if price_rent is not None:
                    type_row.append(f"{price_rent:.1f}€")
                else:
                    type_row.append('')

                if roi is not None:
                    type_row.append(f"{roi:.1f} mesi")
                else:
                    type_row.append('')

                dt.add_row(type_row)

            # Collecting chart prices
            tip_cod = int(row['cod_tip'])

            if tip_cod in prop_types:
                if tip_cod not in chart_price_types:
                    chart_price_types[tip_cod] = {
                        'description': row['descr_tipologia'],
                        'count_sell': 0,
                        'count_rent': 0,
                        'prices': []
                    }
                chart_price_types[tip_cod]['prices'].append({
                    'time_sort': int(row['year']) + (int(row['semester']) - 1)/2,
                    'semester': f"{row['year']} S{row['semester']}",
                    'price_sell': price_sell,
                    'price_rent': price_rent
                })
                if price_sell is not None:
                    chart_price_types[tip_cod]['count_sell'] += 1
                if price_rent is not None:
                    chart_price_types[tip_cod]['count_rent'] += 1

        chart_data = sorted(chart_price_types.items(), key=lambda item: (-len(item[1]['prices']), prop_types.index(item[0])))
        chart_price = []

        if len(chart_data)>0:
            timeseries_selected = chart_data[0][1]
            chart_price = sorted(timeseries_selected['prices'], key=lambda x: x['time_sort'])
            chart_label = timeseries_selected['description']
            chart_embed = {
                'prices': chart_price,
                'label': chart_label,
                'show_sell': (timeseries_selected['count_sell'] >= 0 and timeseries_selected['count_sell'] >= timeseries_selected['count_rent']),
                'show_rent': (timeseries_selected['count_rent'] >= 0 and timeseries_selected['count_rent'] >= timeseries_selected['count_sell'])
            }
            chart_content = f"""
            <p>{chart_label}</p>
            <div class="pi-chart">
                <svg id="pi-chart-prices"></svg>
                <script id="pi-chart-prices-data" type="application/json">{json.dumps(chart_embed)}</script>
            </div>
            """
        else:
            chart_content = ''

        div_html = f"""<div class="pi-ss-pane">
                        <p>Dati mediati sui prezzi di vendita e affitto, utilizzati nelle valutazioni ufficiali degli immobili dall'Agenzia delle Entrate. Dati più dettagliati, inclusi l'intervallo di confidenza e i dati semestrali, sono disponibili nel rapporto esteso.</p>
                        {dt.get_html()}
                        {chart_content}
                    </div>"""

        div_html += f"""<div class="pi-data-table-note">
                Le informazioni sui prezzi di vendita e di affitto sono fornite dall'Agenzia delle Entrate sulla base delle quotazioni OMI e vengono utilizzate per le valutazioni ufficiali degli immobili.
                </div>"""

        return {
            "result": "success",
            "point": point,
            "title": address,
            "data": prices,
            "time_series": chart_price,
            "html": div_html
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
