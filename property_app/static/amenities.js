const activePage = 'amenities';

const amenities = {
    supermarket: {
        'amenity_type': 'supermarket',
        'color': 'yellow',
        'label': 'Supermarket',
        icon: 'supermarket.png',
        mapicon: 'supermarketmap.png'
    },
    store: {
        'amenity_type': 'store',
        'color': 'crimson',
        'label': 'Convenience store',
        icon: 'store.png',
        mapicon: 'convenstoremap.png'
    },
    restaurant: {
        'amenity_type': 'restaurant',
        'color': 'lightblue',
        'label': 'Restaurant',
        icon: 'restaurant.png',
        mapicon: 'restaurantmap.png'
    },
    cafe: {
        'amenity_type': 'cafe',
        'color': 'navy',
        'label': 'Cafe',
        icon: 'cafe.png',
        mapicon: 'cafemap.png'
    },
    medical: {
        'amenity_type': 'medical',
        'color': 'red',
        'label': 'Hospital',
        icon: 'doctor.png',
        mapicon: 'medicalmap.png'
    },
    pub: {
        'amenity_type': 'pub',
        'color': 'orange',
        'label': 'Pub',
        icon: 'pub.png',
        mapicon: 'pubmap.png'
    },
    park: {
        'amenity_type': 'park',
        'color': 'green',
        'label': 'Green space',
        icon: 'park.png',
        mapicon: 'parksmap.png'
    },
    sport: {
        'amenity_type': 'sport',
        'color': 'blue',
        'label': 'Fitness',
        icon: 'sport.png',
        mapicon: 'fitnessmap.png'
    },
};

function updateSectionMap(){
    let loc = PIGetSelectedLocation();

    if (loc === null) {
        PIEmptyPointProcess();
        return;
    }

    PIActivateCircles([loc.lng, loc.lat], [3000]);

    jQuery.post({
        url: '/api/amenities',
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({
            'point': [loc.lng, loc.lat]
        }),
        success: function (data) {
            processUpdateResponse(data);
        }
    });
}

function processUpdateResponse(data) {

    if (data.html !== undefined){
        jQuery("#pi-section-placeholder").html(data.html);
        PIAmenityActivateSubsection(Object.keys(amenities)[0])
    }else{
        jQuery("#pi-section-placeholder").html('');
    }

    if (data.title !== undefined){
        jQuery("#pi-location-title").text(data.title)
    }
    console.log(data);
}

function PIAmenityActivateSubsection(amenity){
    console.log(amenity);
}

map.on('load', () => {

    for (let amt in amenities) {
        map.loadImage(
            `https://property.puzyrkov.com/static/images/amenities/${amenities[amt]['mapicon']}`,
            (error, image) => {
                if (error) throw error;
                map.addImage('image-' + amt, image);
            }
        )
    }

    map.addSource('amenities',
        {
            type: 'vector',
            url: 'https://property.puzyrkov.com/tiles/prop_amenities',
            promoteId: 'osm_id'
        }
    );

    map.addLayer({
        id: 'am-point',
        type: 'symbol',
        'minzoom': 8,
        source: 'amenities',
        'source-layer': 'prop_amenities',
        layout: {
            'icon-image': [
                'match',
                ['get', 'amenity_type'],
                'supermarket',
                'image-supermarket',
                'store',
                'image-store',
                'restaurant',
                'image-restaurant',
                'cafe',
                'image-cafe',
                'pub',
                'image-pub',
                'park',
                'image-park',
                'sport',
                'image-sport',
                'medical',
                'image-medical',
                /* using supermarket image for default icon, since Mapbox requires something for default */
                'image-supermarket'
            ],
            'icon-size': 0.66,
        }
    });

    map.addSource('selected-point', {
        type: 'geojson',
        data: null
    });

    map.addLayer({
        id: 'point-highlight',
        type: 'line',
        source: 'selected-point',
        paint: {
            'line-color': '#0437F2',
            'line-width': 2
        }
    });

    map.on('click', 'am-point', amenityClick);
    map.on('mouseenter', 'am-point', (e) => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'am-point', (e) => {
        map.getCanvas().style.cursor = '';
    });

    updateSectionMap();
});

function amenityClick(e) {

    let props = e.features[0].properties;

    let name = props.name
    if (name === undefined) {
        name = amenities[props.amenity_type].label;
    }

    new mapboxgl.Popup()
        .setLngLat(e.lngLat)
        .setHTML(name)
        .addTo(map);
}

jQuery(document).ready(function(){

    jQuery(document).on('click', '.pi-amenity-button', function(){
        jQuery(this).addClass('pi-amenity-button-active');
    })
})