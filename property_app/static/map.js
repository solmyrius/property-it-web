const mPerDegree = 111320;

function PIGetUserParam(key) {

    const currentData = PILoadUserSettings()

    if(currentData[key] !== undefined){
        return(currentData[key]);
    }else{
        return null;
    }
}

function PIGetSelectedLocation(){

    const currentData = PILoadUserSettings()

    if(currentData.currentLocation !== undefined){
        return(currentData.currentLocation);
    }else{
        return null;
    }
}

function PILoadUserSettings() {
    let dataStr = localStorage.getItem("pi_data");
    if (dataStr === null) {
        return {};
    } else {
        return JSON.parse(dataStr);
    }
}

function PIStoreUserSettings(data) {

    let currentData = PILoadUserSettings();
    for(let i in data){
        currentData[i] = data[i];
    }

    localStorage.setItem("pi_data", JSON.stringify(currentData));
}

function PIStoreSelectedLocation(location){

    PIStoreUserSettings({
        'currentLocation': location
    })
}

function PIMapSelectPoint(e){

    PIStoreSelectedLocation({
        'lng': e.lngLat.lng,
        'lat': e.lngLat.lat,
    });

    PIUpdateSectionMap();
}

function PIEmptyPointProcess() {

    console.log("Point is empty");
}

function PICalculateCirclePoints(center, radiusInM, points=32) {
    const coords = {
        latitude: center[1],
        longitude: center[0]
    };
    const ring = [];
    for (let i = 0; i < points; i++) {
        const angle = (360 / points) * i;
        const latitude = coords.latitude + (radiusInM / mPerDegree) * Math.cos(angle * Math.PI / 180);
        const longitude = coords.longitude + (radiusInM / mPerDegree) / Math.cos(coords.latitude * Math.PI / 180) * Math.sin(angle * Math.PI / 180);
        ring.push([longitude, latitude]);
    }
    ring.push(ring[0]);
    return ring;
}

function PIActivateCircles(center, radii){

    let sourceFeatures = {
        type: "FeatureCollection",
        features: []
    };

    for (const r of radii) {
        sourceFeatures.features.push({
            type: 'Feature',
            geometry: {
                type: 'Polygon',
                coordinates: [PICalculateCirclePoints(center, r)]
            }
        })
    }

    if (map.getSource('point-marker')) {
        map.getSource('point-marker').setData(sourceFeatures);
    } else {
        map.addSource('point-marker', {
            type: 'geojson',
            data: sourceFeatures
        });
    }

    if (map.getLayer('point-marker-line')) {
        // nope
    } else {
        map.addLayer({
            id: 'point-marker-line',
            type: 'line',
            source: 'point-marker',
            layout: {},
            paint: {
                'line-color': 'navy',
                'line-width': 2
            }
        });
    }

    let maxR = Math.max(radii);

    const earthRadius = 6378137;

    const offsetLat = (maxR / earthRadius) * (180 / Math.PI);
    const offsetLng = (maxR / earthRadius) * (180 / Math.PI) / Math.cos(center[1]* Math.PI / 180);

    const northwest = [center[0] - offsetLng, center[1] + offsetLat];
    const southeast = [center[0] + offsetLng, center[1] - offsetLat];

    map.fitBounds([northwest, southeast], {padding: 40});
}

map.on('click', PIMapSelectPoint);