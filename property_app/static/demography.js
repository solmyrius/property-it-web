var selectedDemoSection = 'combined';
var hoveredStateId = null;
var selectedFeatures = [];

const demoLayers = {
    "education": {
        "index": "edu_idx",
        "percentiles":[9.49, 9.72, 9.89, 10.02, 10.15, 10.3, 10.5]
    } ,
    "institutional": {
        "index": "hh_idx",
        "percentiles":[0.0, 0.0001, 0.031, 0.174, 0.36, 0.6355, 1.136]
    },
    "unoccupied": {
        "index": "dwell_idx",
        "percentiles":[15.32625, 20.87, 27.22, 34.435, 42.7, 51.4375, 62.96]
    },
    "homeless": {
        "index": "hless_idx",
        "percentiles":[0.18, 0.31, 0.47, 0.66, 0.94, 1.4725, 2.7]
    },
    "camp": {
        "index": "camp_idx",
        "percentiles":[0.14625, 0.34, 0.57, 1.005, 1.6624999999999999, 2.685, 4.42875]
    },
}

const palette = ["#ff0000", "#ff4500", "#ff8c00", "#ffd700", "#ffff00", "#ccff00", "#7fff00", "#00ff00"];

function PIActivateDemoSection(section){

    selectedDemoSection = section;
    PIActivateDemographyTable();

    jQuery(".pi-dc").removeClass('pi-dc-active');
    jQuery(`[data-demography=${section}]`).addClass('pi-dc-active');

    if (demoLayers[section] !== undefined){

        let colors = palette;
        if (section !== 'education'){
            colors = palette.slice().reverse();
        }

        let colorRule = [
            "step",
            ["to-number", ["get", demoLayers[section]["index"]]]
        ]
        for (let i=0; i<8; i++){
            colorRule.push(colors[i]);
            if (i<7){
                colorRule.push(demoLayers[section]["percentiles"][i])
            }
        }

        let fillColor = [
            'case',
            ['==', ['feature-state', 'hover'], true], '#3bb2d0',
            colorRule
        ];
        map.setPaintProperty('commune', 'fill-color', fillColor);
    }
}

function PIActivateDemographyTable(){

    jQuery('.pi-data-table').hide();
    jQuery('#pi-demography-'+selectedDemoSection).show();
}

function PIUpdateSectionMap() {
    let loc = PIGetSelectedLocation();

    if (loc === null) {
        PIEmptyPointProcess();
        return;
    }

    const point = [loc.lng, loc.lat]

    jQuery.post({
        url: '/api/demography',
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({
            'point': point
        }),
        success: function (data) {
            PIProcessUpdateResponseDemography(data);
        }
    });
}

function PIProcessUpdateResponseDemography(data) {

    if (data.bbox !== undefined) {
        console.log(data.bbox);
        map.fitBounds(data.bbox, {padding: 40});
    }

    if (data.html !== undefined){
        jQuery("#pi-section-placeholder").html(data.html);
    }else{
        jQuery("#pi-section-placeholder").html('');
    }

    if (data.title !== undefined){
        jQuery("#pi-location-title").text(data.title)
    }

    PIActivateDemographyTable();

    selectedFeatures.forEach(function(ftId){
        map.setFeatureState(
            {source: 'census-commune', sourceLayer: 'prop_census_commune_map', id: ftId},
            {'selected-state': false}
        );
    })
    selectedFeatures = [];

    if (data.selected !== undefined){
        map.setFeatureState(
            {source: 'census-commune', sourceLayer: 'prop_census_commune_map', id: data.selected},
            {'selected-state': 'selected'}
        );
        selectedFeatures.push(data.selected);
    }
    if (data.nearby !== undefined){
        data.nearby.forEach(function(ftId){
            map.setFeatureState(
                {source: 'census-commune', sourceLayer: 'prop_census_commune_map', id: ftId},
                {'selected-state': 'nearby'}
            );
            selectedFeatures.push(ftId);
        });
    }
}

function PISectionMapClick(e) {

    PIMapSelectPoint([e.lngLat.lng, e.lngLat.lat]);
}

map.on('load', () => {

    map.addSource('census-commune',
        {
            type: 'vector',
            url: 'https://property.puzyrkov.com/tiles/prop_census_commune_map',
            promoteId: 'commune_id'
        }
    );

    map.addLayer({
        id: 'commune',
        type: 'fill',
        minzoom: 3,
        source: 'census-commune',
        'source-layer': 'prop_census_commune_map',
        layout: {},
        paint: {
            'fill-color': [
                'case',
                ['boolean', ['feature-state', 'hover'], false],
                '#3bb2d0',
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
        id: 'commune-contour',
        type: 'line',
        minzoom: 3,
        source: 'census-commune',
        'source-layer': 'prop_census_commune_map',
        layout: {},
        paint: {
            'line-color': '#08191a',
            'line-width': [
                'case',
                ['==', ['feature-state', 'selected-state'], 'selected'], 3,
                ['==', ['feature-state', 'selected-state'], 'nearby'], 0.5,
                0
            ],
        }
    });

    PIActivateDemoSection('education');

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
                    {source: 'census-commune', sourceLayer: 'prop_census_commune_map', id: hoveredStateId},
                    {hover: false}
                );
            }
            hoveredStateId = e.features[0].id;
            map.setFeatureState(
                {source: 'census-commune', sourceLayer: 'prop_census_commune_map', id: hoveredStateId},
                {hover: true}
            );
        }
    });

    map.on('mouseleave', 'commune', (e) => {
        map.getCanvas().style.cursor = '';

        if (hoveredStateId !== null) {
            map.setFeatureState(
                {source: 'census-commune', sourceLayer: 'prop_census_commune_map', id: hoveredStateId},
                {hover: false}
            );
            hoveredStateId = null;
        }
    });

    var popup = new mapboxgl.Popup({
        // closeButton: false,
        // closeOnClick: false
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

    PIUpdateSectionMap();
});

jQuery(document).ready(function(){

    jQuery(document).on('click', '.pi-dc', function(){

        PIActivateDemoSection(jQuery(this).data('demography'));
    })
})