function PIGetSelectedLocation(){

    const currentData = PILoadUserSettings()

    if(currentData.currentLocation !== undefined){
        return(currentData.currentLocation);
    }else{
        return null;
    }
}

function PILoadUserSettings() {
    let dataStr = sessionStorage.getItem("pi_data");
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

    sessionStorage.setItem("pi_data", JSON.stringify(currentData));
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

    updateSectionMap();
}

function PIEmptyPointProcess() {

    console.log("Point is empty");
}

map.on('click', PIMapSelectPoint);