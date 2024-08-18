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
    doctor: {
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
    pharmacy:{
        mapicon: 'medicalmap.png'
    }
};

function PIUpdateSectionMap(){

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
            PIProcessUpdateResponse(data);
        }
    });
}

function PIProcessUpdateResponse(data) {

    if (data.html !== undefined){
        jQuery("#pi-section-placeholder").html(data.html);
        PIUpdateAmtFilter();
    }else{
        jQuery("#pi-section-placeholder").html('');
    }

    if (data.title !== undefined){
        jQuery("#pi-location-title").text(data.title)
    }
}

function PIUpdateAmtFilter() {

    let selectedAmenities = PIGetUserParam('selected_amenities');
    if (selectedAmenities === null || selectedAmenities.length === 0) {
        selectedAmenities = ['all'];
    }

    let obj = jQuery('#pi-amenity-table');
    if (selectedAmenities.includes('all')) {
        jQuery('.pi-amenity-button').removeClass('pi-amenity-button-active');
        jQuery('.pi-amenity-button[data-amenity=all]').addClass('pi-amenity-button-active');
        obj.find('tr').show();
    }else{
        jQuery('.pi-amenity-button[data-amenity=all]').removeClass('pi-amenity-button-active');
        for(let amt in amenities) {
            if (selectedAmenities.includes(amt)) {
                jQuery(`.pi-amenity-button[data-amenity=${amt}]`).addClass('pi-amenity-button-active');
                obj.find(`[data-amenity=${amt}]`).show();
            }else{
                jQuery(`.pi-amenity-button[data-amenity=${amt}]`).removeClass('pi-amenity-button-active');
                obj.find(`[data-amenity=${amt}]`).hide();
            }
        }
    }
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

    PIUpdateSectionMap();
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

    PIUpdateAmtFilter();

    jQuery(document).on('click', '.pi-amenity-button', function(){
        let selectedAmenities = PIGetUserParam('selected_amenities');
        if (selectedAmenities === null){
            selectedAmenities = []
        }

        let obj = jQuery(this);
        let amt = obj.data('amenity');

        if (amt === 'all') {
            selectedAmenities = ['all'];

            if (obj.hasClass('pi-amenity-button-active')){
                obj.removeClass('pi-amenity-button-active');
            }else{
                obj.addClass('pi-amenity-button-active');
            }
        }else{

            if (obj.hasClass('pi-amenity-button-active')){
                let idx = selectedAmenities.indexOf(amt);
                if(idx>-1){
                    selectedAmenities.splice(idx, 1);
                }
                obj.removeClass('pi-amenity-button-active');
            }else{
                let idx = selectedAmenities.indexOf(amt);
                if(idx<0){
                    selectedAmenities.push(amt);
                }
                obj.addClass('pi-amenity-button-active');

                let indexAll = selectedAmenities.indexOf('all');
                if (indexAll>-1){
                    selectedAmenities.splice(indexAll, 1);
                }
            }
        }


        PIStoreUserSettings({'selected_amenities': selectedAmenities});
        PIUpdateAmtFilter();
    })
})