import json
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


def home(request):
    return HttpResponse('Hello, welcome to my Django page!')


def ui_section(request, section):

    map_template = f"section_{section}.html"
    map_script_url = f"/static/{section}.js"

    section_rules = [
        {
            'section': 'overview',
            'anchor': 'Overview',
            'href': '/overview'
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
        }
    ]

    # Setting the active menu item
    active_menu = section

    context = {
        'sub_template': 'page_map.html',
        'map_template': map_template,
        'map_script_url': map_script_url,
        'top_menu': section_rules,
        'active_menu': active_menu,
        'section': section
    }

    section_info = {}
    for ss in section_rules:
        if ss['section'] == section:
            section_info = ss

    if section == 'amenities':
        from classes.data_amenity import DataAmenity
        data_class = DataAmenity()
        context['amenities_buttons'] = data_class.get_buttons()
    if section == 'demography':
        from classes.data_demography import DataDemography
        data_class = DataDemography()
    if section == 'scuole':
        from classes.data_schools import DataSchools
        data_class = DataSchools

    location_placeholder = "all'indirizzo selezionato in Italia"
    context['head_title'] = section_info['title'].replace('{placeholder}', location_placeholder)
    context['page_title'] = section_info['title'].replace('{placeholder}', '<span id="pi-location-title">'+location_placeholder+'</span>')
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
        if section == 'amenities':
            from classes.data_amenity import DataAmenity
            data_class = DataAmenity()
        if section == 'demography':
            from classes.data_demography import DataDemography
            data_class = DataDemography()
        if section == 'scuole':
            from classes.data_schools import DataSchools
            data_class = DataSchools()

        if data_class is not None:
            return JsonResponse(data_class.get_section_data(data['point']))

    resp = HttpResponse("Wrong request")
    resp.status_code = 400
    return resp
