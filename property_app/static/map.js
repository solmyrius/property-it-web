const mPerDegree = 111320;

function PIGetUserParam(key) {

    const currentData = PILoadUserSettings()

    if (currentData[key] !== undefined) {
        return (currentData[key]);
    } else {
        return null;
    }
}

function PIGetSelectedLocation() {

    const currentData = PILoadUserSettings()

    if (currentData.currentLocation !== undefined) {
        return (currentData.currentLocation);
    } else {
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
    for (let i in data) {
        currentData[i] = data[i];
    }

    localStorage.setItem("pi_data", JSON.stringify(currentData));
}

function PIStoreSelectedLocation(location) {

    PIStoreUserSettings({
        'currentLocation': location
    })
}

function PIMapSelectPoint(point) {

    PIStoreSelectedLocation({
        'lng': point[0],
        'lat': point[1],
    });

    PIUpdateSectionMap();
}

function PIEmptyPointProcess() {

    console.log("Point is empty");
}

function PICalculateCirclePoints(center, radiusInM, points = 32) {
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

function PINavigateCircles(center, radii) {
    PIActivatePoint(center);
    PIActivateCircles(center, radii);

    let maxR = Math.max(radii);

    const earthRadius = 6378137;

    const offsetLat = (maxR / earthRadius) * (180 / Math.PI);
    const offsetLng = (maxR / earthRadius) * (180 / Math.PI) / Math.cos(center[1] * Math.PI / 180);

    const northwest = [center[0] - offsetLng, center[1] + offsetLat];
    const southeast = [center[0] + offsetLng, center[1] - offsetLat];

    map.fitBounds([northwest, southeast], {padding: 40});
}

function PINavigateArea(center, polygon) {
    PIActivatePoint(center);

    console.log(polygon);
    let lngs = [];
    let lats = [];
    if(polygon.type.toLowerCase()==='polygon'){
        lngs = polygon.coordinates[0].map(point => point[0]);
        lats = polygon.coordinates[0].map(point => point[1]);
    }else if (polygon.type.toLowerCase()==='multipolygon') {
        lngs = polygon.coordinates[0][0].map(point => point[0]);
        lats = polygon.coordinates[0][0].map(point => point[1]);
    }

    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);
    let bounds = [[minLng, minLat], [maxLng, maxLat]];

    let w = bounds[1][0] - bounds[0][0];
    let h = bounds[1][1] - bounds[0][1];
    let b2 = [[bounds[0][0] - w/2, bounds[0][1] - h/2], [bounds[1][0] + w/2, bounds[1][1] + h/2]];
    map.fitBounds(b2, {padding: 40});
}

function PIActivatePoint(center) {
    const pointSource =
        {
            type: "FeatureCollection",
            features: [
                {
                    type: 'Feature',
                    geometry: {
                        type: 'Point',
                        coordinates: center
                    }
                }
            ]
        };
    if (map.getSource('point-marker')) {
        map.getSource('point-marker').setData(pointSource);
    } else {
        map.addSource('point-marker', {
            type: 'geojson',
            data: pointSource
        });
    }

    if (map.getLayer('point-marker')) {
        // nope
    } else {
        map.addLayer({
            id: 'point-marker',
            type: 'circle',
            source: 'point-marker',
            layout: {},
            paint: {
                'circle-color': 'crimson',
                'circle-radius': 6,
                'circle-stroke-width': 1,
                'circle-stroke-color': '#000'
            }
        });
    }
}

function PIActivateCircles(center, radii) {

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

    if (map.getSource('point-marker-circles')) {
        map.getSource('point-marker-circles').setData(sourceFeatures);
    } else {
        map.addSource('point-marker-circles', {
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
            source: 'point-marker-circles',
            layout: {},
            paint: {
                'line-color': 'navy',
                'line-width': 2
            }
        });
    }
}

let sectionMapLocation = {'lng': 9.19828, 'lat': 45.46193};
let sectionMapZoom = 9;
let sectionMapLocationEmbed = document.getElementById("pi-section-map-location");
if(sectionMapLocationEmbed !== null){
    let sectionMapData = JSON.parse(sectionMapLocationEmbed.innerText);
    if (sectionMapData.zoom !== undefined){
        sectionMapZoom = sectionMapData.zoom
    }
    if (sectionMapData.center !== undefined){
        sectionMapLocation = sectionMapData.center
    }
}

const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/outdoors-v11',
    // style: {version: 8,sources: {},layers: []},
    center: sectionMapLocation,
    zoom: sectionMapZoom
});

const geocoder = new MapboxGeocoder({
        accessToken: mapboxgl.accessToken,
        mapboxgl: mapboxgl,
        countries: 'IT'
    });
map.addControl(geocoder, 'top-left');

map.on('load', () => {
    map.on('click', PISectionMapClick);  // Should process click on blank map only
})
