class DataTable:
    def __init__(self):
        self.columns = 3
        self.row_header = []
        self.rows_body = []

    def put_header(self, row):
        self.row_header = row
        self.columns = len(row)

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