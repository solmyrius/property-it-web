function PIUpdateSectionMap(){

    let loc = PIGetSelectedLocation();

    if (loc === null) {
        PIEmptyPointProcess();
        return;
    }

    PINavigateCircles([loc.lng, loc.lat], [500]);

    jQuery.post({
        url: '/api/scuole',
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({
            'point': [loc.lng, loc.lat]
        }),
        success: function (data) {
            PIProcessUpdateResponseScuole(data);
        }
    });
}

function PIProcessUpdateResponseScuole(data){

    console.log(data);
}

function PISectionMapClick(e) {
    if (map.queryRenderedFeatures(e.point).filter(feature => feature.source === 'amenities').length === 0) {
        PIMapSelectPoint([e.lngLat.lng, e.lngLat.lat]);
    }
}

map.on('load', () => {

    map.addSource('scuole',
        {
            type: 'vector',
            url: 'https://property.puzyrkov.com/tiles/prop_schools_geo',
            promoteId: 'school_id'
        }
    );

    map.addSource('selected-point', {
        type: 'geojson',
        data: null
    });

    map.addLayer({
        id: 'scoule-point',
        type: 'circle',
        source: 'scuole',
        'source-layer': 'prop_schools_geo',
        layout: {},
        paint: {
            'circle-color': [
                'match',
                ['get', 'is_state'],
                'state', '#4682B4',
                'crimson' // Default color
            ],
            'circle-radius': 6,
            'circle-stroke-width': 1,
            'circle-stroke-color': '#000'
        }
    });

    PIUpdateSectionMap();
});