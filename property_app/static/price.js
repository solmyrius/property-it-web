var hoveredStateId = null;

function PIUpdateSectionMap() {

    PIUpdateMapColors();

    let loc = PIGetSelectedLocation();

    if (loc === null) {
        PIEmptyPointProcess();
        return;
    }

    PINavigateCircles([loc.lng, loc.lat], [3000]);

    jQuery.post({
        url: '/api/omi',
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

    if (data.html !== undefined) {
        jQuery("#pi-section-placeholder").html(data.html);
    } else {
        jQuery("#pi-section-placeholder").html('');
    }

    if (data.title !== undefined) {
        jQuery("#pi-location-title").text(data.title)
    }

    PIActivatePriceCharts();
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

const palette = ["#ff0000", "#ff4500", "#ff8c00", "#ffd700", "#ffff00", "#ccff00", "#7fff00", "#00ff00"];
const perc = [533.4375, 670.0, 800.0, 925.0, 1080.0, 1300.0, 1700.0]

function PIUpdateMapColors() {

    let colors = palette;

    let colorRule = [
        "step",
        ["to-number", ["get", 'ps_20']],
    ]
    for (let i = 0; i < 8; i++) {
        colorRule.push(colors[i]);
        if (i < 7) {
            colorRule.push(perc[i])
        }
    }

    let fillColor = [
        'case',
        ['==', ['feature-state', 'hover'], true], '#3bb2d0',
        ['==', ['get', 'ps_20'], null], '#0055ff',
        colorRule
    ];
    map.setPaintProperty('price-zone-fill', 'fill-color', fillColor);
}

function PIActivatePriceCharts() {
    const chart_embed = JSON.parse(jQuery('#pi-chart-prices-data').text());
    const data = chart_embed.prices;

    const width = 600, height = 500;
    const margin = {top: 20, right: 50, bottom: 50, left: 50};
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const svg = d3.select("#pi-chart-prices")
        .attr("viewBox", `0 0 ${width} ${height}`)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Scales
    const x = d3.scalePoint()
        .domain(data.map(d => d.semester))
        .range([0, innerWidth]);

    // Axes
    svg.append("g")
        .attr("transform", `translate(0,${innerHeight})`)
        .call(d3.axisBottom(x))
        .selectAll("text")
        .attr("transform", "rotate(80)")
        .style("text-anchor", "start");

    // Tooltip
    const tooltip = d3.select("body").append("div")
        .attr("class", "tooltip")
        .style("position", "absolute")
        .style("background-color", "#f9f9f9")
        .style("border", "1px solid #d3d3d3")
        .style("padding", "5px")
        .style("border-radius", "5px")
        .style("opacity", 0);

    // Add Legend
    const legend = svg.append("g")
        .attr("transform", `translate(40, ${margin.top})`); // Positioning on the left of the chart

    if (chart_embed.show_sell) {
        const ySell = d3.scaleLinear()
            .domain([d3.min(data, d => d.price_sell) - 10, d3.max(data, d => d.price_sell) + 10])
            .nice()
            .range([innerHeight, 0]);

        svg.append("g").call(d3.axisLeft(ySell));

        const lineSell = d3.line()
            .x(d => x(d.semester))
            .y(d => ySell(d.price_sell));

        svg.append("path")
            .datum(data)
            .attr("fill", "none")
            .attr("stroke", "steelblue")
            .attr("stroke-width", 2)
            .attr("d", lineSell);

        svg.selectAll("circle.sell")
            .data(data)
            .enter()
            .append("circle")
            .attr("class", "sell")
            .attr("cx", d => x(d.semester))
            .attr("cy", d => ySell(d.price_sell))
            .attr("r", 4)
            .attr("fill", "steelblue")
            .on("mouseover", function (event, d) {
                tooltip.transition().duration(200).style("opacity", .9);
                tooltip.html(`Semester: ${d.semester}<br>Sell Price: ${d.price_sell}`)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 28) + "px");
            })
            .on("mouseout", function () {
                tooltip.transition().duration(500).style("opacity", 0);
            });

        legend.append("rect")
            .attr("x", 0)
            .attr("y", 0)
            .attr("width", 10)
            .attr("height", 10)
            .attr("fill", "steelblue");

        legend.append("text")
            .attr("x", 15)
            .attr("y", 10)
            .text("Sell Price")
            .style("font-size", "12px")
            .attr("alignment-baseline", "middle");
    }

    if (chart_embed.show_rent) {
        const yRent = d3.scaleLinear()
            .domain([d3.min(data, d => d.price_rent) - 10, d3.max(data, d => d.price_rent) + 10])
            .nice()
            .range([innerHeight, 0]);

        svg.append("g")
            .attr("transform", `translate(${innerWidth},0)`)
            .call(d3.axisRight(yRent));

        const lineRent = d3.line()
            .x(d => x(d.semester))
            .y(d => yRent(d.price_rent));

        svg.append("path")
            .datum(data)
            .attr("fill", "none")
            .attr("stroke", "orange")
            .attr("stroke-width", 2)
            .attr("d", lineRent);

        // Add points for Rent price with tooltip
        svg.selectAll("circle.rent")
            .data(data)
            .enter()
            .append("circle")
            .attr("class", "rent")
            .attr("cx", d => x(d.semester))
            .attr("cy", d => yRent(d.price_rent))
            .attr("r", 4)
            .attr("fill", "orange")
            .on("mouseover", function (event, d) {
                tooltip.transition().duration(200).style("opacity", .9);
                tooltip.html(`Semester: ${d.semester}<br>Rent Price: ${d.price_rent}`)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 28) + "px");
            })
            .on("mouseout", function () {
                tooltip.transition().duration(500).style("opacity", 0);
            });

        legend.append("rect")
            .attr("x", 0)
            .attr("y", 20)
            .attr("width", 10)
            .attr("height", 10)
            .attr("fill", "orange");

        legend.append("text")
            .attr("x", 15)
            .attr("y", 30)
            .text("Rent Price")
            .style("font-size", "12px")
            .attr("alignment-baseline", "middle");
    }
}


function PISectionMapClick(e) {

    PIMapSelectPoint([e.lngLat.lng, e.lngLat.lat]);
}

map.on('load', () => {

    map.addSource('omi-price',
        {
            type: 'vector',
            url: 'https://property.puzyrkov.com/tiles/prop_omi_geo',
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
        'source-layer': 'prop_omi_geo',
        type: 'fill',
        minzoom: 3,
        layout: {},
        paint: {
            'fill-color': [
                'case',
                ['boolean', ['feature-state', 'hover'], false], '#3bb2d0',
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
        'source-layer': 'prop_omi_geo',
        type: 'line',
        minzoom: 3,
        layout: {},
        paint: {
            'line-color': '#08191a',
            'line-width': [
                'case',
                ['==', ['feature-state', 'selected-state'], 'selected'], 3,
                0
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
                    {source: 'omi-price', sourceLayer: 'prop_omi_geo', id: hoveredStateId},
                    {hover: false}
                );
            }
            hoveredStateId = e.features[0].id;
            map.setFeatureState(
                {source: 'omi-price', sourceLayer: 'prop_omi_geo', id: hoveredStateId},
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