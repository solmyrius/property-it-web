import json
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


def home(request):
    return HttpResponse('Hello, welcome to my Django page!')


def ui_section(request, section):

    map_template = f"section_{section}.html"
    map_script_url = f"/static/{section}.js"

    top_menu = [
        {
            'section': 'overview',
            'anchor': 'Overview',
            'href': '/overview'
        },
        {
            'section': 'amenities',
            'anchor': 'Amenities',
            'href': '/amenities'
        }
    ]

    # Setting the active menu item
    active_menu = section

    context = {
        'sub_template': 'page_map.html',
        'map_template': map_template,
        'map_script_url': map_script_url,
        'top_menu': top_menu,
        'active_menu': active_menu,
        'section': section
    }
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

        if data_class is not None:
            return JsonResponse(data_class.get_section_data(data['point']))

    resp = HttpResponse("Wrong request")
    resp.status_code = 400
    return resp
