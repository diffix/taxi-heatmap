function updateFilter() {
    const tChoice = parseInt(document.getElementById('tSlider').value, 10);
    filterBy(tChoice);
}

function filterBy(hourOfDay) {
    let filters = ['==', 'hourOfDay', hourOfDay];

    for (dataSetConf of conf.dataSets) {
        const mapElement = dataSetConf.kind === 'raw' ? rawMap : dataSetConf.kind === 'baseline' ? baselineMap : syndiffixMap
        
        mapElement.setFilter(dataSetConf.name + '-heatRectangles-fareAmounts', filters);
        mapElement.setFilter(dataSetConf.name + '-heatRectangles-counts', filters);
        mapElement.setFilter(dataSetConf.name + '-values-fareAmounts', filters);
        mapElement.setFilter(dataSetConf.name + '-values-counts', filters);
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
        const layerSuffixes = ['heatRectangles-fareAmounts', 'heatRectangles-counts',
                               'values-fareAmounts', 'values-counts',
                               'rectangles' ]
        const mapElement = dataSetConf.kind === 'raw' ? rawMap : dataSetConf.kind === 'baseline' ? baselineMap : syndiffixMap
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
    mapboxgl.clearStorage(error => {
        if (error) {
            console.error("mapboxgl.clearStorage returned", error);
        } else {
            console.log("mapboxgl.clearStorage success");
        }
    });
    rawMap = new mapboxgl.Map({
        container: 'rawMap',
        style: mapboxStyleUrl,
        center: startCenter,
        zoom: startZoom
    });
    baselineMap = new mapboxgl.Map({
        container: 'baselineMap',
        style: mapboxStyleUrl,
        center: startCenter,
        zoom: startZoom
    });
    syndiffixMap = new mapboxgl.Map({
        container: 'syndiffixMap',
        style: mapboxStyleUrl,
        center: startCenter,
        zoom: startZoom
    });
    rawMap.on('load', function () {
        prepareMap();
        updateFilter();
        updateDataSet();
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
    const container1 = '#comparison-container1';

    const compare1Object = new mapboxgl.Compare(rawMap, baselineMap, container1, {});
    const container2 = '#comparison-container2';

    const compare2Object = new mapboxgl.Compare(rawMap, syndiffixMap, container2, {});

    // This adds the +/- zoom thingy. Adding in both maps, to not have to figure out how to block the slider from
    // running over it.
    rawMap.addControl(new mapboxgl.NavigationControl());
    baselineMap.addControl(new mapboxgl.NavigationControl());
    syndiffixMap.addControl(new mapboxgl.NavigationControl());

    initializeLegend()
    initializeSwipers(compare1Object, compare2Object)
}

function initializeLegend() {
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
}

function initializeSwipers(compare1Object, compare2Object) {
    const rawText = "Original"
    const baselineText = "Synthetic data by mostly.ai"
    const syndiffixText = "Synthetic data by <a href=\"https://open-diffix.org\" target=\"_blank\" rel=\"noopener noreferrer\">Syn-Diffix</a>"

    const captionRaw = document.createElement('div')
    const captionRawContent = document.createElement('h2')
    captionRawContent.textContent = rawText
    captionRaw.appendChild(captionRawContent)
    captionRaw.className = 'map-overlay1-caption-left'
    const captionBaseline = document.createElement('div')
    const captionBaselineContent = document.createElement('h2')
    captionBaselineContent.innerHTML = baselineText
    captionBaseline.appendChild(captionBaselineContent)
    captionBaseline.className = 'map-overlay1-caption-right'

    const compare1 = document.getElementsByClassName('mapboxgl-compare')[0]
    compare1.appendChild(captionBaseline)
    compare1.appendChild(captionRaw)

    const caption2Left = document.createElement('div')
    const caption2LeftContent = document.createElement('h2')
    caption2LeftContent.innerHTML = baselineText
    caption2Left.appendChild(caption2LeftContent)
    caption2Left.className = 'map-overlay2-caption-left'
    const captionSyndiffix = document.createElement('div')
    const captionSyndiffixContent = document.createElement('h2')
    captionSyndiffixContent.innerHTML = syndiffixText
    captionSyndiffix.appendChild(captionSyndiffixContent)
    captionSyndiffix.className = 'map-overlay2-caption-right'

    const compare2 = document.getElementsByClassName('mapboxgl-compare')[1]
    compare2.appendChild(captionSyndiffix)
    compare2.appendChild(caption2Left)

    const compareSwiper1 = compare1.getElementsByClassName('compare-swiper-vertical')[0]
    const compareSwiper2 = compare2.getElementsByClassName('compare-swiper-vertical')[0]

    function onMouseTouchMove() {
        if (compare2Object.currentPosition < compare1Object.currentPosition) {
            captionRaw.hidden = true
            captionBaseline.hidden = true
            caption2LeftContent.innerHTML = rawText
            compareSwiper1.style.opacity = "0.3"
        } else {
            captionRaw.hidden = false
            captionBaseline.hidden = false
            caption2LeftContent.innerHTML = baselineText
            compareSwiper1.style.opacity = "initial"
        }
    }
    function onTouchEnd() {
        document.removeEventListener("touchmove", onMouseTouchMove);
        document.removeEventListener("touchend", onTouchEnd);
    }
    function onMouseUp() {
        document.removeEventListener("mousemove", onMouseTouchMove);
        document.removeEventListener("mouseup", onMouseUp);
    }
    function onMouseTouchDown(event) {
        event.touches ? (document.addEventListener("touchmove", onMouseTouchMove), document.addEventListener("touchend", onTouchEnd)) :
                      (document.addEventListener("mousemove", onMouseTouchMove), document.addEventListener("mouseup", onMouseUp));
    }

    compareSwiper1.addEventListener("mousedown", onMouseTouchDown); 
    compareSwiper1.addEventListener("touchstart", onMouseTouchDown); 
    compareSwiper2.addEventListener("mousedown", onMouseTouchDown); 
    compareSwiper2.addEventListener("touchstart", onMouseTouchDown); 

    // Offset both sliders to the sides so they're not over each other.
    compare1Object.setSlider(compare1Object.currentPosition * 2 / 3);
    compare2Object.setSlider(compare2Object.currentPosition * 4 / 3);
}

function prepareMap() {
    // Assuming that the coarsest comes first here.
    const maxGeoWidth = conf.dataSets[0].geoWidth;
    const minGeoWidth = conf.dataSets[conf.dataSets.length - 1].geoWidth;
    for (dataSetConf of conf.dataSets) {
        if (dataSetConf.kind === 'raw') {
            addDataSet(rawMap, dataSetConf, minGeoWidth, maxGeoWidth)
        } else if (dataSetConf.kind === 'baseline') {
            addDataSet(baselineMap, dataSetConf, minGeoWidth, maxGeoWidth)
        } else if (dataSetConf.kind === 'syndiffix') {
            addDataSet(syndiffixMap, dataSetConf, minGeoWidth, maxGeoWidth)
        }
    }
}

function addDataSet(mapElement, dataSetConf, minGeoWidth, maxGeoWidth) {
    const geoWidth = parseFloat(dataSetConf.geoWidth);
    const zoomOffset = Math.log2(geoWidth / 0.0001).toFixed(1); // ~2-5
    const minZoomHeatmapMaxGeoWidth = 0
    const minZoomHeatmap = (geoWidth == maxGeoWidth ? minZoomHeatmapMaxGeoWidth : 17.5 - zoomOffset);
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

    function addPolygonsLayer(mapElement, valuePlottedData, expression, lowest, average, highest) {
        mapElement.addLayer({
            id: dataSetConf.name + '-heatRectangles-' + valuePlottedData,
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
                                expression,
                                lowest, colorLowest,
                                average, colorAvg,
                                highest, colorHighest
                            ],
                'fill-opacity': [
                    'interpolate',
                    ['linear'],
                    ['zoom'],
                    minZoomHeatmapMaxGeoWidth, 0,
                    11, 0.8,
                    15.5, 0.8,
                    16.5, 0.6
                ],
                'fill-outline-color': 'rgba(255,255,255,0)'
            }
        }, 'waterway-label');
    }

    function addCentersLayer(mapElement, valuePlottedData, expression) {
        mapElement.addLayer({
            id: dataSetConf.name + '-values-' + valuePlottedData,
            type: 'symbol',
            source: dataSetConf.name + '-centers',
            minzoom: minZoom,
            maxzoom: maxZoom,
            layout: {
                'visibility': 'none',
                'text-allow-overlap': true,
                'text-ignore-placement': true,
                'text-field': ['to-string', expression],
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
    }

    addPolygonsLayer(mapElement, 'fareAmounts', ['get', 'fare_amounts'], 0.0, 11.6, 70.0);
    // FIXME: adjust average and highest
    addPolygonsLayer(mapElement, 'counts', ['get', 'count'], 0.0, 10.0, 10000.0);

    addCentersLayer(mapElement, 'fareAmounts', ['get', 'fare_amounts']);
    addCentersLayer(mapElement, 'counts', ['get', 'count']);

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
let rawMap = null
let baselineMap = null
let syndiffixMap = null
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
