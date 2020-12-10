var width = 960;
var height = 500;
var g_lat0=-90, g_lat1=90, g_lon0=-180, g_lon1=180;

var map = {
    projection: d3.geoEquirectangular(),
    // projection: d3.geoOrthographic(),
    bbox: makeRangeBox(),
    canvas: d3.select("#chart").append("canvas")
        .attr("id", "main-canvas")
        .attr("width", width)
        .attr("height", height),
    sketch: d3.select("body").append("custom:sketch")
        .attr("width", width)
        .attr("height", height),
    data: null,
    features: null,
    custom: d3.select(document.createElement('custom')),  // dummy
    canvas_hidden: d3.select("#chart").append("canvas")
        .attr("id", "hidden-canvas")
        .attr("width", width)
        .attr("height", height)
        .attr("style", "display: none")
};
map.context = map.canvas.node().getContext('2d');
map.context_hidden = map.canvas_hidden.node().getContext('2d');


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

function drawMap(map, features, hidden) {
    context = hidden ? map.context_hidden : map.context;
    var path = d3.geoPath(map.projection, context)

    features.forEach(function(d, i) {
        context.save()

        context.beginPath()
        path(d)
        context.closePath()

        context.fillStyle = hidden ? null : 'rgba(255,255,255,0.5)';
        context.strokeStyle = hidden ? null : 'black';
        context.fill()
        context.stroke()

        context.restore()
    })
}

function zoomed(e) {
    var transform = e.transform
    map.context.save();
    map.context.clearRect(0, 0, width, height);
    map.context.translate(transform.x, transform.y);
    map.context.scale(transform.k, transform.k);
    drawMap(map, map.features)
    drawHeatMap(map, map.data)
    map.context.restore();
}

function setZoom(map) {
    map.canvas.call(d3.zoom().scaleExtent([1, 8]).on("zoom",  zoomed))
}

// map to track color the nodes.
var colorToNode = {};
// function to create new colors for picking
var nextCol = 1;
function genColor() {
    var ret = [];
    ret.push(nextCol & 0xff); //R
    ret.push((nextCol & 0xff00) >> 8); //G
    ret.push((nextCol & 0xff0000) >> 16); //B

    nextCol += 200;
    var col = "rgb(" + ret.join(',') + ")";
    return col;
}

function drawHeatMap(map, hidden) {
    // var path = d3.geoPath(map.projection, map.context)
    context = hidden ? map.context_hidden : map.context;
    var paths = map.custom.selectAll('path')
    context.save();

    paths.each(function(d, i) {
        if (d === undefined) {
            return
        }
        node = d3.select(this)
        parent_ = d3.select(this.parentElement)
        var p = new Path2D(d)
        context.fillStyle = hidden ? parent_.attr("fillStyleHidden") : parent_.attr("fill")
        context.strokeStyle = hidden ? parent_.attr("fillStyleHidden") : parent_.attr("fill")
        context.fill(p)
        if (!hidden) {
            context.stroke(p)
        }
    })

    context.restore();
}

function computePaths(data) {
    var minTemp = -6, maxTemp = 6;
    var cmap = d3.scaleSequential().domain([minTemp, maxTemp])
        .interpolator(d3.interpolateViridis); 

    var path = d3.geoPath(map.projection)

    g = map.custom.selectAll('custom')
        .data(data.values)
        .enter().append('custom')
            .attr('fill', d => cmap(d))
            .attr('stroke', d => cmap(d))
            .attr('fillStyleHidden', function(d, i) {
                c = genColor();
                colorToNode[c] = {
                    temp: d,
                    lat: data.lat[Math.floor(i / data.width)],
                    lon: data.lon[i % data.width],
                }
                return c
            })
    map.custom.selectAll('custom')
        .datum(function(d, i) {
            d = data.values[i]
            map.context.beginPath()
            var r = Math.floor(i / data.width)
            var c = i % data.width
            if (c >= data.width - 1 || r >= data.height - 1) {
                return null
            }
            var lon0 = data.lon[c]
            var lon1 = data.lon[c+1]
            var lat0 = data.lat[r]
            var lat1 = data.lat[r+1]
            return path(makeRectPolygon(lon0, lon1, lat0, lat1))
        }).append('path')
}

function registerMouseOver() {
    d3.select("#main-canvas").on('mousemove', function(e) {
        var x = e.layerX || e.offsetX;
		var y = e.layerY || e.offsety;
        var c = map.context_hidden.getImageData(x, y, 1, 1).data;
        var colKey = 'rgb(' + c[0] + ',' + c[1] + ',' + c[2] + ')';
		var nodeData = colorToNode[colKey];

        console.log(e.x, e.y)

        if (nodeData) {
            d3.select('#tooltip')
                .style('opacity', 0.8)
                .style('top', e.pageY + 5 + 'px')
                .style('left', e.pageX + 5 + 'px')
                .html(
                    'temp = ' + Number.parseFloat(nodeData.temp).toFixed(2)
                    + '<br> lon = ' + Number.parseFloat(nodeData.lon).toFixed(1)
                    + '<br> lat = ' + Number.parseFloat(nodeData.lat).toFixed(1)
                )
        } else {
            d3.select('#tooltip')
                .style('opacity', 0)
        }
    })
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

    // draw heatmap
    map.data = ovtData
    computePaths(map.data)
    drawHeatMap(map)
    // drawHeatMap(map, true)

    // draw basemap
    var features = topojson.feature(worldMap, worldMap.objects.countries).features;
    map.features = features

    drawMap(map, features);

    // register mouseover tooltip
    registerMouseOver()

    // set zoom callback
    // setZoom(map)
}

function setProj() {
    // extent = d3.geoPath(map.projection).bounds(map.bbox);
    // map.projection = map.projection.clipExtent(extent);
    map.projection = map.projection.fitExtent(
        [[10, 10], [width - 10, height - 10]], map.bbox
    );
}
