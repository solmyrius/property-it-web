import json
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


def home(request):
    return HttpResponse('Hello, welcome to my Django page!')


def section_rules():
    return [
        {
            'section': 'sintesi',
            'title': 'Sintesi vicino a {placeholder}',
            'anchor': 'Sintesi',
            'href': '/sintesi'
        },
        {
            'section': 'demography',
            'title': "Profilo demografico dell'area vicino a {placeholder}",
            'anchor': 'Demography',
            'href': '/demography'
        },
        {
            'section': 'amenities',
            'title': 'Servizi locali vicino a {placeholder}',
            'anchor': 'Amenities',
            'href': '/amenities'
        },
        {
            'section': 'scuole',
            'title': 'Scuole vicino a {placeholder}',
            'anchor': 'Scuole',
            'href': '/scuole'
        },
        {
            'section': 'price',
            'title': 'Property prices in the region of {placeholder}',
            'anchor': 'Property prices',
            'href': '/price'
        },
        {
            'section': 'ambiente',
            'title': 'I fattori ambientali nella regione {placeholder}',
            'anchor': 'Ambiente',
            'href': '/ambiente'
        }
    ]


def ui_section(request, section):
    map_template = f"section_{section}.html"
    map_script_url = f"/static/{section}.js"

    sections = section_rules()

    # Setting the active menu item
    active_menu = section

    context = {
        'sub_template': 'page_map.html',
        'map_template': map_template,
        'map_script_url': map_script_url,
        'top_menu': sections,
        'active_menu': active_menu,
        'section': section
    }

    section_info = {}
    for ss in sections:
        if ss['section'] == section:
            section_info = ss

    if section == 'sintesi':
        pass
    if section == 'amenities':
        from classes.data_amenity import DataAmenity
        data_class = DataAmenity()
        context['amenities_buttons'] = data_class.get_buttons()
    if section == 'demography':
        from classes.data_demography import DataDemography
        data_class = DataDemography()
    if section == 'scuole':
        from classes.data_schools import DataSchools
        data_class = DataSchools()

    location_placeholder = "all'indirizzo selezionato in Italia"
    context['head_title'] = section_info['title'].replace('{placeholder}', location_placeholder)
    context['page_title'] = section_info['title'].replace('{placeholder}',
                                                          '<span id="pi-location-title">' + location_placeholder + '</span>')
    context['section_content'] = '<div id="pi-section-placeholder"></div>'

    return render(request, 'page.html', context)


@csrf_exempt
def api_section(request, section):
    if request.method == 'POST':
        data = json.loads(request.body)
        """
        data = {
            'point': [lng, lat]
        }
        """
        data_class = None
        if section == 'sintesi':
            from classes.data_overview import DataOverview
            data_class = DataOverview()
        if section == 'amenities':
            from classes.data_amenity import DataAmenity
            data_class = DataAmenity()
        if section == 'demography':
            from classes.data_demography import DataDemography
            data_class = DataDemography()
        if section == 'scuole':
            from classes.data_schools import DataSchools
            data_class = DataSchools()
        if section == 'omi':
            from classes.data_omi import DataOmi
            data_class = DataOmi()

        if data_class is not None:
            return JsonResponse(data_class.get_section_data(data['point']))

    resp = HttpResponse("Wrong request")
    resp.status_code = 400
    return resp


def ui_school(request, school_id):
    from classes.data_schools import DataSchools
    data_class = DataSchools()
    school_info = data_class.get_school_data(school_id)

    context = {
        'sub_template': 'page_map.html',
        'map_template': 'scuola.html',
        'map_script_url': '/static/scuola.js',
        'top_menu': section_rules(),
        'active_menu': 'scuole',
        'section': '',
        'head_title': f"Informazioni dettagliate sulla scuola selezionata: {school_info['school']['denominazionescuola']}",
        'page_title': f"""Informazioni dettagliate sulla scuola selezionata: <span id="pi-location-title">{school_info['school']['denominazionescuola']}</span>""",
        'section_content': school_info["html"]
    }

    return render(request, 'page.html', context)
