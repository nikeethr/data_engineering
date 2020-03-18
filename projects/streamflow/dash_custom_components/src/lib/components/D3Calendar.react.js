import * as d3 from 'd3';
import './D3Calendar.css';

const MONTHS_SHORT = [
    'jan', 'feb', 'mar', 'apr', 'may', 'jun',
    'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
]

const DAYS_IN_WEEK = 7
const GRID_SIZE = 12  // px
const GRID_SPACING = 2  // px

function plotMonthGrids(monthGrids, el) {
    var divs = monthGrids.selectAll('.month-grid')
        .data(
            function(d) { return d.values; },
            function(d) { return d.key; }
        )

    divs.exit().remove()

    var divsEnter = divs.enter()
        .append('div')

    divsEnter
        .append('svg')
        .append('g')
            .attr('class', 'month-grid-group')

    var merged = divsEnter
        .merge(divs)

    merged
        .attr('class', 'month-grid')

    var gs = merged.select('g.month-grid-group')

    var rects = gs.selectAll('rect')
        .data(function(d) {
            const OFFSET = d.values[0].date.getDay()
            for (var i = 0; i < d.values.length; i++) {
                d.values[i].pos = i + OFFSET
            }
            return d.values;
        }, function(d) { return d.date.toString(); } )


    rects.exit().remove()

    rects.enter().append('rect')

    rects
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
        .on('click', function(d, i) {
            el.dispatchEvent(new CustomEvent('click_data', { detail: d }));
        })

    var svgs = merged.select('svg')
    svgs
        .attr('width', function(d, i) {
            var g = this.childNodes[0];
            return g.getBBox().width
        })
        .attr('height', function(d, i) {
            var g = this.childNodes[0];
            return g.getBBox().height
        })
}

function plotCalendar(nestedData, el) {
    var chart = d3.select(el)
    var divYearsData = chart.selectAll('.row-year').data(
        nestedData, function(d) { return d.key; }
    )

    var exit = divYearsData.exit().remove()

    var divYearsEnter = divYearsData
        .enter().append('div')

    divYearsEnter
        .append('div')
            .attr('class', 'year-heading')
        .append('h1')
            .text(function(d) { return d.key })

    divYearsEnter.append('div')
        .attr('class', 'month-grid-container')

    var merged = divYearsEnter
        .merge(divYearsData)

    merged
        .attr('id', function(d) { return 'year' + '-' + d.key })
        .attr('class', 'row-year')

    plotMonthGrids(merged.select('.month-grid-container'), el)
}


/* Main */
function plot(data, el) {
    var parseTime = d3.timeParse('%Y-%m-%d')
    var data_copy = new Array(data.length)

    for (var i = 0; i < data_copy.length; i++) {
        data_copy[i] = {
            date: parseTime(data[i].date),
            value: parseFloat(data[i].value)
        }
    }

    var nestedData = d3.nest()
        .key(function(d) { return d.date.getFullYear() })
    .key(function(d) { return d.date.getFullYear() +
        '-' + MONTHS_SHORT[d.date.getMonth()] } )
        .entries(data_copy)

    plotCalendar(nestedData, el)
}

const D3Calendar = {};

D3Calendar.create = (el, data, bindEvents) => {
    // D3 Code to create the chart
    plot(data, el)
    bindEvents()
};

D3Calendar.update = (el, data, bindEvents) => {
    // D3 Code to update the chart
    plot(data, el)
    bindEvents()
};

D3Calendar.destroy = () => {
    // Cleaning code here
};


export default D3Calendar;
