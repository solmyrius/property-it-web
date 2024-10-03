var hoveredStateId = null;

function PIUpdateSectionMap() {

    let loc = PIGetSelectedLocation();

    if (loc === null) {
        PIEmptyPointProcess();
        return;
    }

    PINavigateCircles([loc.lng, loc.lat], [3000]);

    jQuery.post({
        url: '/api/price',
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({
            'point': [loc.lng, loc.lat]
        }),
        success: function (data) {
            PIProcessUpdateResponsePrice(data);
        }
    });
}

function PIProcessUpdateResponsePrice(data) {

    if (data.html !== undefined){
        jQuery("#pi-section-placeholder").html(data.html);
    }else{
        jQuery("#pi-section-placeholder").html('');
    }

    if (data.title !== undefined){
        jQuery("#pi-location-title").text(data.title)
    }
}

function PIPriceZoneClick(e) {

    var coordinates = e.lngLat;
    var properties = e.features[0].properties;
    var description = '<div class="popup-content">';
    for (var key in properties) {
        description += `<p>${key}: <b>${properties[key]}</b></p>`;
    }
    description += '</div>';
    new mapboxgl.Popup()
        .setLngLat(coordinates)
        .setHTML(description)
        .addTo(map);
}

function PISectionMapClick(e) {

    PIMapSelectPoint([e.lngLat.lng, e.lngLat.lat]);
}

map.on('load', () => {

    map.addSource('omi-price',
        {
            type: 'vector',
            url: 'https://property.puzyrkov.com/tiles/prop_omi_shapes',
            promoteId: 'link_zona'
        }
    );

    map.addSource('selected-point', {
        type: 'geojson',
        data: null
    });

    map.addLayer({
        id: 'price-zone-fill',
        source: 'omi-price',
        'source-layer': 'prop_omi_shapes',
        type: 'fill',
        minzoom: 3,
        layout: {},
        paint: {
            'fill-color': [
                'case',
                ['boolean', ['feature-state', 'hover'], false], '#3bb2d0',
                ['==', ['get', 'fascia'], 'R'], '#00ff00',
                ['==', ['get', 'fascia'], 'B'], '#ff0000',
                ['==', ['get', 'fascia'], 'C'], 'orange',
                ['==', ['get', 'fascia'], 'D'], 'yellow',
                ['==', ['get', 'fascia'], 'E'], '#9ACD32',
                '#ffffff'
            ],
            'fill-opacity': [
                'case',
                ['boolean', ['feature-state', 'hover'], false],
                0.75,       // Highlight opacity
                0.5         // Default opacity
            ]
        }
    });

    map.addLayer({
        id: 'price-zone-line',
        source: 'omi-price',
        'source-layer': 'prop_omi_shapes',
        type: 'line',
        minzoom: 3,
        layout: {},
        paint: {
            'line-color': '#08191a',
            'line-width': [
                'case',
                ['==', ['feature-state', 'selected-state'], 'selected'], 3,
                0.5
            ],
        }
    });

    map.on('mouseenter', 'price-zone-fill', (e) => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('click', 'price-zone-fill', (e) => {
        PIPriceZoneClick(e);
    });

    map.on('mousemove', 'price-zone-fill', (e) => {
        if (e.features.length > 0) {
            if (hoveredStateId !== null) {
                map.setFeatureState(
                    {source: 'omi-price', sourceLayer: 'prop_omi_shapes', id: hoveredStateId},
                    {hover: false}
                );
            }
            hoveredStateId = e.features[0].id;
            map.setFeatureState(
                {source: 'omi-price', sourceLayer: 'prop_omi_shapes', id: hoveredStateId},
                {hover: true}
            );
        }
    });

    map.on('mouseleave', 'price-zone-fill', (e) => {
        map.getCanvas().style.cursor = '';

        if (hoveredStateId !== null) {
            map.setFeatureState(
                {source: 'omi-price', sourceLayer: 'prop_omi_shapes', id: hoveredStateId},
                {hover: false}
            );
            hoveredStateId = null;
        }
    });

    PIUpdateSectionMap();
});