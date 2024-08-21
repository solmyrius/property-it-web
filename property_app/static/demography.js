var hoveredStateId = null;

function PIUpdateSectionMap() {

}

map.on('load', () => {

    map.addSource('census-commune',
        {
            type: 'vector',
            url: 'https://property.puzyrkov.com/tiles/fn_census',
            promoteId: 'commune_id'
        }
    );

    map.addLayer({
        id: 'commune',
        type: 'fill',
        minzoom: 3,
        source: 'census-commune',
        'source-layer': 'fn_census',
        paint: {
            'fill-color': [
                'case',
                ['boolean', ['feature-state', 'selected'], false],
                '#3bb2d0',
                [
                    "step",
                    ["to-number", ["get", "edu_idx"]],
                    "#FFC0CB",
                    9.49,
                    "#D4AAB2",
                    9.72,
                    "#AA9599",
                    9.89,
                    "#808080",
                    10.02,
                    "#55AA55",
                    10.15,
                    "#6DE457",
                    10.3,
                    "#24F61D",
                    10.5,
                    "#00FF00"
                ]
            ],
            'fill-opacity': [
                'case',
                ['boolean', ['feature-state', 'hover'], false],
                0.75,       // Highlight opacity
                0.5         // Default opacity
            ],
            'fill-outline-color': 'navy'
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

    map.on('mouseenter', 'commune', (e) => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mousemove', 'commune', (e) => {
        if (e.features.length > 0) {
            if (hoveredStateId !== null) {
                map.setFeatureState(
                    {source: 'census-commune', sourceLayer: 'fn_census', id: hoveredStateId},
                    {hover: false}
                );
            }
            hoveredStateId = e.features[0].id;
            map.setFeatureState(
                {source: 'census-commune', sourceLayer: 'fn_census', id: hoveredStateId},
                {hover: true}
            );
        }
    });

    map.on('mouseleave', 'commune', (e) => {
        map.getCanvas().style.cursor = '';

        if (hoveredStateId !== null) {
            map.setFeatureState(
                {source: 'census-commune', sourceLayer: 'fn_census', id: hoveredStateId},
                {hover: false}
            );
            hoveredStateId = null;
        }
    });

    var popup = new mapboxgl.Popup({
        closeButton: false,
        closeOnClick: false
    });

    map.on('click', 'commune', function(e) {
        if (e.features.length > 0) {
            var coordinates = e.features[0].geometry.coordinates.slice();
            var name = e.features[0].properties.name;

            // Ensure that if the map is zoomed out such that multiple
            // copies of the feature are visible, the popup appears
            // over the copy being pointed to.
            while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
                coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
            }

            let html=`<p>Name: <b>${name}</b></p>`;
            html += `<p>Education index: <b>${e.features[0].properties.edu_idx}</b></p>`

            popup.setLngLat(e.lngLat)
                .setHTML(html)
                .addTo(map);
        }
    });
});
