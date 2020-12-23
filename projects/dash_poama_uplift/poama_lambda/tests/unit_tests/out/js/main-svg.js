var width = 960;
var height = 500;
var svg = d3.select("#chart")
    .append("svg")
    .attr("width", width)
    .attr("height", height)
//  .attr("viewport", [0, 0, width, height]);
//  .call(d3.zoom().scaleExtent([1, 8]).on('zoom', zoomed));
var g_all = svg.append('g')

var map = {
    projection: d3.geoEquirectangular(),
    // projection: d3.geoOrthographic(),
    bbox: makeRangeBox(),
    heatmap: g_all.append('g'),
    basemap: g_all.append('g')
};


function zoomed(e) {
    g_all.attr('transform', e.transform);
}


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

const promises = [
    d3.json("https://unpkg.com/world-atlas@1/world/110m.json"),
    d3.json(g_plotDataUrl)
]
Promise.all(promises).then(plotMap)

function plotMap(data) {
    // draw basemap
    var worldMap = data[0];
    var ovtData = data[1];

    setProj();
    var path = d3.geoPath(map.projection);

    map.basemap.selectAll("path").data(
        topojson.feature(worldMap, worldMap.objects.countries).features
    ).enter().append("path")
        .attr('d', path)
        .attr('fill', 'white')
        .attr('opacity', 0.5)
        .attr('stroke', 'white')
        .attr('stroke-width', 1)

    // color scale
    temp_range = d3.extent(ovtData.values)
    var minTemp = temp_range[0], maxTemp = temp_range[1];
    var cmap = d3.scaleSequential().domain([minTemp, maxTemp])
        .interpolator(d3.interpolateViridis); 

    // draw grids
    map.heatmap.selectAll("path").data(ovtData.values)
        .enter().append("path")
        .attr('delay', function(d, i) { return i })
        .attr('data-lon', function(d, i) { return ovtData.lon[i % ovtData.width] })
        .attr('data-lat', function(d, i) { return ovtData.lat[Math.floor(i / ovtData.width)] })
        .attr('d', function(d, i) {
            var r = Math.floor(i / ovtData.width)
            var c = i % ovtData.width
            if (c >= ovtData.width - 1 || r >= ovtData.height - 1) {
                return null
            }
            var lon0 = ovtData.lon[c]
            var lon1 = ovtData.lon[c+1]
            var lat0 = ovtData.lat[r]
            var lat1 = ovtData.lat[r+1]
            ret = path(makeRectPolygon(lon0, lon1, lat0, lat1))
            return ret
        })
        .attr("fill", function(d) { return cmap(d) })
        .attr("stroke", function(d) { return cmap(d) })
        .on("mouseover", function(e) {
            elem = d3.select(this)
            elem.attr("fill", "black")
            data_ = {
                lon: elem.attr('data-lon'),
                lat: elem.attr('data-lat'),
                temp: elem.datum()
            }
            d3.select('#tooltip')
                .style('opacity', 0.8)
                .style('top', e.pageY + 5 + 'px')
                .style('left', e.pageX + 5 + 'px')
                .html(
                    'temp = ' + Number.parseFloat(data_.temp).toFixed(2)
                    + '<br> lon = ' + Number.parseFloat(data_.lon).toFixed(1)
                    + '<br> lat = ' + Number.parseFloat(data_.lat).toFixed(1)
                )
        })
        .on("mouseout", function(d, i) {
            elem = d3.select(this)
            elem.attr("fill", d => cmap(d))
            d3.select('#tooltip')
                .style('opacity', 0)
        })

        // adjust svg rect
        bbox = map.heatmap.node().getBoundingClientRect()
        g_all.attr("transform", "translate(" + -bbox.left + "," + -bbox.top + ")")
        svg.attr("width", bbox.width)
        svg.attr("height", bbox.height)
}

function setProj() {
    // extent = d3.geoPath(map.projection).bounds(map.bbox);
    // map.projection = map.projection.clipExtent(extent);
    map.projection = map.projection.fitExtent(
        [[10, 10], [width - 10, height - 10]], map.bbox
    );
}
