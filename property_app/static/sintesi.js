function PIUpdateSectionMap() {

    let loc = PIGetSelectedLocation();

    if (loc === null) {
        PIEmptyPointProcess();
        return;
    }

    PINavigateCircles([loc.lng, loc.lat], [3000]);

    jQuery.post({
        url: '/api/sintesi',
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({
            'point': [loc.lng, loc.lat]
        }),
        success: function (data) {
            PIProcessUpdateResponseSintesi(data);
        }
    });
}

function PIProcessUpdateResponseSintesi(data) {

    if (data.html !== undefined){
        jQuery("#pi-section-placeholder").html(data.html);
    }else{
        jQuery("#pi-section-placeholder").html('');
    }

    if (data.title !== undefined){
        jQuery("#pi-location-title").text(data.title)
    }
}

function PISectionMapClick(e) {
    if (map.queryRenderedFeatures(e.point).filter(feature => feature.source === 'amenities').length === 0) {
        PIMapSelectPoint([e.lngLat.lng, e.lngLat.lat]);
    }
}

map.on('load', () => {

    PIUpdateSectionMap();
});