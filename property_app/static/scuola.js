function PIScuoleClick(e) {

    let props = e.features[0].properties;

    let name = props.name
    if (name === undefined) {
        name = 'Scuola';
    }

    new mapboxgl.Popup()
        .setLngLat(e.lngLat)
        .setHTML(name)
        .addTo(map);

}

function PISectionMapClick(e) {
    if (map.queryRenderedFeatures(e.point).filter(feature => feature.source === 'scuole').length === 0) {
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
        id: 'scoule-marker',
        type: 'circle',
        source: 'scuole',
        'source-layer': 'prop_schools_geo',
        layout: {},
        paint: {
            'circle-color': [
                'match',
                ['get', 'is_state'],
                'state', '#4682B4',
                'private', '#7CFC00',
                'white' // Default color
            ],
            'circle-radius': 6,
            'circle-stroke-width': 1,
            'circle-stroke-color': '#000'
        }
    });

    map.on('click', 'scoule-marker', PIScuoleClick);
    map.on('mouseenter', 'scoule-marker', (e) => {
        map.getCanvas().style.cursor = 'pointer';
    });
    map.on('mouseleave', 'scoule-marker', (e) => {
        map.getCanvas().style.cursor = '';
    });

    const scuolaLocationEmbed = document.getElementById("pi-section-map-location");
    if(scuolaLocationEmbed !== null){
        const scuolaLocation = JSON.parse(scuolaLocationEmbed.innerText);
        const scuolaMarker = new mapboxgl.Marker()
            .setLngLat(scuolaLocation.center)
            .addTo(map);
    }
});