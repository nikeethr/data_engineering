MONTHS_SHORT = [
    'jan', 'feb', 'mar', 'apr', 'may', 'jun',
    'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
]

DAYS_IN_WEEK = 7
GRID_SIZE = 12  // px
GRID_SPACING = 2  // px
D_MAX = 2  // TODO: compute this don't guess


function plotMonthGrids(monthGrids) {
    divs = monthGrids.selectAll('.month-grid')
        .data(function(d) {
            return d.values;
        })
        .enter()
        .append('div')
            .attr('class', 'month-grid')

    svgs = divs.append('svg')
    gs = svgs.append('g')

    gs.selectAll('rect')
        .data(function(d) {
            OFFSET = d.values[0].date.getDay()
            for (i = 0; i < d.values.length; i++) {
                d.values[i].pos = i + OFFSET
            }
            return d.values;
        })
        .enter()
        .append('rect')
            .attr('x', function(d) {
                return (d.pos % DAYS_IN_WEEK) * (GRID_SIZE + GRID_SPACING)
            })
            .attr('y', function(d) {
                return ((d.pos / DAYS_IN_WEEK) >> 0) * (GRID_SIZE + GRID_SPACING)
            })
            .attr('width', GRID_SIZE)
            .attr('height', GRID_SIZE)
            .attr('fill', function(d) { return d3.interpolateViridis(d.value) })
            .attr('class', '.grid-rect')

    svgs
        .attr('width', function(d, i) {
            g = this.childNodes[0];
            return g.getBBox().width
        })
        .attr('height', function(d, i) {
            g = this.childNodes[0];
            return g.getBBox().height
        })
}

function plotCalendar(nestedData) {
    chart = d3.select('#chart')
    divYears = chart.selectAll('.row-year')
        .data(nestedData).enter()
        .append('div')
            .attr('id', function(d) { return 'year' + '-' + d.key })

    yearHeading = divYears
        .append('div')
            .attr('class', 'year-heading')
        .append('h1')
            .text(function(d) { return d.key })

    monthGrids = divYears.append('div')
        .attr('class', 'month-grid-container')

    plotMonthGrids(monthGrids)
}


/* Main */
var parseTime = d3.timeParse('%Y-%m-%d')
d3.csv('/data/random_data.csv').then(function(data) {
    data.forEach(function(d, i) {
        d.date = parseTime(d.date)
        d.value = parseFloat(d.value)
    })


    function getWeekOfMonth(d) {
        day = d.date.getDate()
        return (day / DAYS_IN_WEEK) >> 0  // convert to int32

    }

    var nestedData = d3.nest()
        .key(function(d) { return d.date.getFullYear() })
        .key(function(d) { return MONTHS_SHORT[d.date.getMonth()] } )
        .entries(data)

    plotCalendar(nestedData)
})
