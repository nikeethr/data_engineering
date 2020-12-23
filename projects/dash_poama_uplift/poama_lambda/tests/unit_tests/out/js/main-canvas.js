var width = 960;
var height = 500;

var map = {
    projection: d3.geoEquirectangular(),
    // projection: d3.geoOrthographic(),
    bbox: makeRangeBox(),
    canvas: d3.select("#chart").append("canvas")
        .attr("id", "main-canvas")
        .attr("width", width)
        .attr("height", height),
    dummy_svg: d3.select("#chart").append("svg")
        .attr("id", "dummy-svg")
        .attr("width", width)
        .attr("height", height),
    sketch: d3.select("body").append("custom:sketch")
        .attr("width", width)
        .attr("height", height),
    data: null,
    features: null,
};
map.context = map.canvas.node().getContext('2d');

function makeRectPolygon(x0, x1, y0, y1) {
    return {
        type: "Polygon",
        coordinates: [[
            [x0, y0],
            [x0, y1],
            [x1, y1],
            [x1, y0],
            [x0, y0]
        ]]
    }
}

function makeRangeBox() {
    // to cross antimeridian w/o ambiguity
    if (g_lon0 > 0 && g_lon1 < 0) {
        g_lon1 += 360
    }

    // to make lat span unambiguous
    if (g_lat0 > g_lat1) {
        var tmp = g_lat0
        g_lat0 = g_lat1
        g_lat1 = tmp
    }

    var dlon4 = (g_lon1 - g_lon0) / 4

    return {
        type: 'Polygon',
        coordinates: [[
            [g_lon0, g_lat0],
            [g_lon0, g_lat1],
            [g_lon0 + dlon4, g_lat1],
            [g_lon0 + 2 * dlon4, g_lat1],
            [g_lon0 + 3 * dlon4, g_lat1],
            [g_lon1, g_lat1],
            [g_lon1, g_lat0],
            [g_lon1 - dlon4, g_lat0],
            [g_lon1 - 2 * dlon4, g_lat0],
            [g_lon1 - 3 * dlon4, g_lat0],
            [g_lon0, g_lat0]
        ]]
    }
}

function drawMap() {
    var context = map.context
    var features = map.features
    var path = d3.geoPath(map.projection, context)

    features.forEach(function(d, i) {
        context.save()

        context.beginPath()
        path(d)
        context.closePath()

        context.fillStyle = 'rgba(255,255,255,0.5)';
        context.strokeStyle = 'black';
        context.fill()
        context.stroke()

        context.restore()
    })
}

function zoomed(e) {
    var transform = e.transform
    map.context.save();
    map.context.clearRect(0, 0, width, height);
    map.context.scale(transform.k, transform.k);
    drawAll()
    map.context.restore();
}

function setZoom(map) {
    map.canvas.call(d3.zoom().scaleExtent([1, 8]).on("zoom",  zoomed))
}


function registerMouseOver() {
    
    d3.select("#main-canvas").on('mousemove', function(e) {
        drawAll(e)
    })
}


function drawAll(e) {
    map.context.clearRect(0, 0, width, height)
    drawHeatMap(e)
    drawMap()
}


function drawHeatMap(e) {
    var path = d3.geoPath(map.projection, map.context)
    var minTemp = -6, maxTemp = 6;
    var cmap = d3.scaleSequential().domain([minTemp, maxTemp])
        .interpolator(d3.interpolateViridis); 
    var data = map.data
    var setTooltip = false
    var tooltipX, tooltipY

    if (e) {
        e.x_ = e.layerX || e.offsetX;
        e.y_ = e.layerY || e.offsety;
    }

    for (var i = 0; i < data.values.length; i++) {
        d = data.values[i]

        if (d === null)
            continue

        var r = Math.floor(i / data.width)
        var c = i % data.width

        if (c >= data.width - 1 || r >= data.height - 1)
            continue

        var lon0 = data.lon[c]
        var lon1 = data.lon[c+1]
        var lat0 = data.lat[r]
        var lat1 = data.lat[r+1]

        map.context.save()

        map.context.beginPath()
        path(makeRectPolygon(lon0, lon1, lat0, lat1))
        map.context.closePath()

        if (e && map.context.isPointInPath(e.x_, e.y_)) {
            setTooltip = true
            tooltipData = {
                x: e.pageX + 5,
                y: e.pageY + 5,
                d: Number.parseFloat(d).toFixed(2),
                lon: Number.parseFloat(((lon0 + lon1) / 2)).toFixed(1),
                lat: Number.parseFloat(((lat0 + lat1) / 2).toFixed(1))
            }
        }

        map.context.fillStyle = cmap(d)
        map.context.fill()

        map.context.restore()
    }

    if (setTooltip) {
        d3.select('#tooltip')
            .style('opacity', 0.8)
            .style('top', tooltipData.y + 'px')
            .style('left', tooltipData.x + 'px')
            .html(
                'temp = ' + tooltipData.d
                + '<br> lon = ' + tooltipData.lon
                + '<br> lat = ' + tooltipData.lat
            )
    } else {
        d3.select('#tooltip')
            .style('opacity', 0)
    }
}

const promises = [
    d3.json("https://unpkg.com/world-atlas@1/world/110m.json"),
    d3.json("/data/ovt_data.json")
]
Promise.all(promises).then(plotMap)

function plotMap(data) {
    var worldMap = data[0];
    var ovtData = data[1];

    setProj();

    map.data = ovtData
    var features = topojson.feature(worldMap, worldMap.objects.countries).features;
    map.features = features

    drawAll()

    // register mouseover tooltip
    registerMouseOver()

    // set zoom callback
    // setZoom(map)
}

function setProj() {
    var path = d3.geoPath(map.projection)
    map.dummy_svg.select('g').remove()
    map.dummy_svg.append('g').append('path')
        .attr('d', path(map.bbox))
    bbox = map.dummy_svg.select('path').node().getBoundingClientRect()

    width = (bbox.width + 20).toFixed(0)
    height = (bbox.height + 20).toFixed(0)

    map.projection = map.projection.fitExtent(
        [[10, 10], [width - 10, height - 10]], map.bbox
    );
    var extent = d3.geoPath(map.projection).bounds(map.bbox);
    map.projection = map.projection.clipExtent(extent);

}
