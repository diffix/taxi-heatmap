function updateFilter() {
    const tChoice = parseInt(document.getElementById('tSlider').value, 10);
    filterBy(tChoice);
}

function filterBy(hourOfDay) {
    let filters = ['==', 'hourOfDay', hourOfDay];

    for (dataSetConf of conf.dataSets) {
        const mapElement = dataSetConf.isRaw ? map2 : map
        mapElement.setFilter(dataSetConf.name + '-heatRectangles-fareAmounts', filters);
        mapElement.setFilter(dataSetConf.name + '-heatRectangles-tripSpeed', filters);
        mapElement.setFilter(dataSetConf.name + '-values-fareAmounts', filters);
        mapElement.setFilter(dataSetConf.name + '-values-tripSpeed', filters);
        mapElement.setFilter(dataSetConf.name + '-rectangles', filters);
    }
    const time = `${hourOfDay.toString().padStart(2, "0")}:00`;
    document.getElementById('time').textContent = 'Time: ' + time;
}

function getValuePlottedData() {
    const radioButtons = document.querySelectorAll('input[name="pdRadio"]');
    let valuePlottedData;
    for (const radioButton of radioButtons) {
        if (radioButton.checked) {
            valuePlottedData = radioButton.value;
            break;
        }
    }
    return valuePlottedData
}

function updateDataSet() {
    for (dataSetConf of conf.dataSets) {
        const layerSuffixes = ['heatRectangles-fareAmounts', 'heatRectangles-tripSpeed',
                               'values-fareAmounts', 'values-tripSpeed',
                               'rectangles' ]
        const mapElement = dataSetConf.isRaw ? map2 : map
        layerSuffixes.forEach((layerSuffix) => {
            mapElement.setLayoutProperty(dataSetConf.name + '-' + layerSuffix, 'visibility', 'none')
        });

        const valuePlottedData = getValuePlottedData()
        mapElement.setLayoutProperty(dataSetConf.name + '-heatRectangles-' + valuePlottedData, 'visibility', 'visible');
        mapElement.setLayoutProperty(dataSetConf.name + '-values-' + valuePlottedData, 'visibility', 'visible');

        mapElement.setLayoutProperty(dataSetConf.name + '-rectangles', 'visibility', 'visible');
    }
}

const mapboxStyleUrl = 'mapbox://styles/mapbox/light-v10';
const startCenter = [-73.935242, 40.730610];
const startZoom = 13;

/*
 * The average fare and speed to gauge the colors with:
 * taxi_heatmap=# SELECT avg(fare_amount) FROM taxi;
 *         avg         
 * --------------------
 *  11.566858325464596
 * (1 row)
 * 
 * taxi_heatmap=# SELECT sum(trip_distance) / NULLIF(sum(trip_time_in_secs), 0) * 3600 FROM taxi;
 *       ?column?      
 * --------------------
 *  14.613886791653774
 * (1 row)
 * 
 * Colors are coming from https://colorbrewer2.org/?type=diverging&scheme=RdYlBu&n=3
 */
const [colorHighest, colorAvg, colorLowest] = ['#fc8d59','#ffffbf','#91bfdb'];

function initializePage(parsed) {
    conf = parsed;
    mapboxgl.accessToken = conf.accessToken;
    map = new mapboxgl.Map({
        container: 'map',
        style: mapboxStyleUrl,
        center: startCenter,
        zoom: startZoom
    });
    map2 = new mapboxgl.Map({
        container: 'map2',
        style: mapboxStyleUrl,
        center: startCenter,
        zoom: startZoom
    });
    map2.on('load', function () {
        prepareMap();
        updateFilter();
        updateDataSet();
        document.title = conf.title;
        document
            .getElementById('tSlider')
            .addEventListener('input', function () {
                updateFilter();
            });
        document
            .querySelectorAll('input[name="pdRadio"]')
            .forEach((radioButton) => radioButton.addEventListener('input', function () {
                updateDataSet();
            }));
    });
    const container = '#comparison-container';
    // FIXME swapped because we want anonymous on the right. Rename things and fix this
    new mapboxgl.Compare(map2, map, container, {});

    // This adds the +/- zoom thingy. Adding in both maps, to not have to figure out how to block the slider from
    // running over it.
    map.addControl(new mapboxgl.NavigationControl());
    map2.addControl(new mapboxgl.NavigationControl());

    const legend = document.getElementById('legend');
    const descriptions = ['High', 'Average', 'Low'].reverse()
    const colors = [colorHighest, colorAvg, colorLowest].reverse();
    const descriptionsRow = document.createElement('tr')
    const colorsRow = document.createElement('tr')
    legend.appendChild(descriptionsRow);
    legend.appendChild(colorsRow);

    colors.forEach((color, i) => {
        const description = descriptions[i];
        const descriptionItem = document.createElement('td');
        const colorItem = document.createElement('td');
        const key = document.createElement('span');
        key.className = 'legend-key';
        key.style.backgroundColor = color;

        const value = document.createElement('span');
        value.innerHTML = `${description}`;
        descriptionItem.appendChild(value);
        colorItem.appendChild(key);
        descriptionsRow.appendChild(descriptionItem);
        colorsRow.appendChild(colorItem);
    });

    const rawCaption = document.createElement('div')
    const rawCaptionContent = document.createElement('h2')
    rawCaptionContent.textContent = "Raw"
    rawCaption.appendChild(rawCaptionContent)
    rawCaption.className = 'map-overlay-caption-left'
    const anonymizedCaption = document.createElement('div')
    const anonymizedCaptionContent = document.createElement('h2')
    anonymizedCaptionContent.textContent = "Anonymized"
    anonymizedCaption.appendChild(anonymizedCaptionContent)
    anonymizedCaption.className = 'map-overlay-caption-right'

    const compare = document.getElementsByClassName('mapboxgl-compare')[0]
    compare.appendChild(anonymizedCaption)
    compare.appendChild(rawCaption)
}

function prepareMap() {
    // Assuming that the coarsest comes first here.
    const maxGeoWidth = conf.dataSets[0].geoWidth;
    const minGeoWidth = conf.dataSets[conf.dataSets.length - 1].geoWidth;
    for (dataSetConf of conf.dataSets) {
        if (dataSetConf.isRaw) {
            addDataSet(map2, dataSetConf, minGeoWidth, maxGeoWidth)
        } else {
            addDataSet(map, dataSetConf, minGeoWidth, maxGeoWidth)
        }
    }
}

function addDataSet(mapElement, dataSetConf, minGeoWidth, maxGeoWidth) {
    const geoWidth = parseFloat(dataSetConf.geoWidth);
    const zoomOffset = Math.log2(geoWidth / 0.0001).toFixed(1); // ~2-5
    const minZoomHeatmap = (geoWidth == maxGeoWidth ? 10 : 17.5 - zoomOffset);
    const minZoom = 17.5 - zoomOffset;
    const maxZoom = (geoWidth == minGeoWidth) ? 20 : 17.5 - zoomOffset + 1;
    
    mapElement.addSource(dataSetConf.name + '-polygons', {
        type: 'geojson',
        data: dataSetConf.polygonsFileRelativePath,
        // increase if you see rendering errors
        buffer: 8
    });
    mapElement.addSource(dataSetConf.name + '-centers', {
        type: 'geojson',
        data: dataSetConf.centersFileRelativePath,
        // increase if you see rendering errors
        buffer: 2
    });
    mapElement.addLayer({
        id: dataSetConf.name + '-heatRectangles-fareAmounts',
        type: 'fill',
        source: dataSetConf.name + '-polygons',
        minzoom: minZoomHeatmap,
        maxzoom: maxZoom,
        layout: {
            'visibility': 'none'
        },
        paint: {
            'fill-color': [
                            'interpolate',
                            ['linear'],
                            ['get', 'fare_amounts'],
                            0.0, colorLowest,
                            11.6, colorAvg,
                            70.0, colorHighest
                        ],
            'fill-opacity': [
                'interpolate',
                ['linear'],
                ['zoom'],
                10, 0,
                11, 0.8,
                15.5, 0.8,
                16.5, 0.6
            ],
            'fill-outline-color': 'rgba(255,255,255,0)'
        }
    }, 'waterway-label');
    mapElement.addLayer({
        id: dataSetConf.name + '-values-fareAmounts',
        type: 'symbol',
        source: dataSetConf.name + '-centers',
        minzoom: minZoom,
        maxzoom: maxZoom,
        layout: {
            'visibility': 'none',
            'text-allow-overlap': true,
            'text-ignore-placement': true,
            'text-field': ['to-string', ['get', 'fare_amounts']],
            'text-size': [
                'interpolate',
                ['exponential', 1.99],
                ['zoom'],
                0, 1,
                22, Math.round(1750000 * geoWidth)
            ]
        },
        paint: {
            'text-opacity': [
                'interpolate',
                ['linear'],
                ['zoom'],
                16.5 - zoomOffset, 0,
                17 - zoomOffset, 0.4,
                21.5 - zoomOffset, 0.4,
                22 - zoomOffset, 0
            ]
        }
    });
    mapElement.addLayer({
        id: dataSetConf.name + '-heatRectangles-tripSpeed',
        type: 'fill',
        source: dataSetConf.name + '-polygons',
        minzoom: minZoomHeatmap,
        maxzoom: maxZoom,
        layout: {
            'visibility': 'none'
        },
        paint: {
            'fill-color': [
                            'interpolate',
                            ['linear'],
                            ['get', 'trip_speed'],
                            0.0, colorLowest,
                            14.6, colorAvg,
                            40.0, colorHighest
                        ],
            'fill-opacity': [
                'interpolate',
                ['linear'],
                ['zoom'],
                10, 0,
                11, 0.8,
                15.5, 0.8,
                16.5, 0.6
            ],
            'fill-outline-color': 'rgba(255,255,255,0)'
        }
    }, 'waterway-label');
    mapElement.addLayer({
        id: dataSetConf.name + '-values-tripSpeed',
        type: 'symbol',
        source: dataSetConf.name + '-centers',
        minzoom: minZoom,
        maxzoom: maxZoom,
        layout: {
            'visibility': 'none',
            'text-allow-overlap': true,
            'text-ignore-placement': true,
            'text-field': ['to-string', ['get', 'trip_speed']],
            'text-size': [
                'interpolate',
                ['exponential', 1.99],
                ['zoom'],
                0, 1,
                22, Math.round(1750000 * geoWidth)
            ]
        },
        paint: {
            'text-opacity': [
                'interpolate',
                ['linear'],
                ['zoom'],
                16.5 - zoomOffset, 0,
                17 - zoomOffset, 0.4,
                21.5 - zoomOffset, 0.4,
                22 - zoomOffset, 0
            ]
        }
    });
    mapElement.addLayer({
        id: dataSetConf.name + '-rectangles',
        type: 'fill',
        source: dataSetConf.name + '-polygons',
        minzoom: minZoom,
        maxzoom: maxZoom,
        layout: {
            'visibility': 'none'
        },
        paint: {
            'fill-color': 'rgba(255,255,255,0)',
            'fill-opacity': [
                'interpolate',
                ['linear'],
                ['zoom'],
                15.5 - zoomOffset, 0,
                16 - zoomOffset, 0.1
            ],
            'fill-outline-color': 'rgb(0,0,0)'
        }
    }, 'waterway-label');
}

const urlParams = new URLSearchParams(window.location.search);
const initialDataSet = urlParams.has('ds') ? parseInt(urlParams.get('ds'), 10) : 0;
let map = null
let map2 = null
let conf = null;

fetch('conf/taxi-heatmap.json')
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json()
    })
    .then(parsed => initializePage(parsed))
    .catch(error => {
        console.error('There has been a problem fetching the conf file:', error)
    });
