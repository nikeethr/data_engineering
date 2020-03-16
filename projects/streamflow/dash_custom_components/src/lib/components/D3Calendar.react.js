import * as d3 from 'd3';
import './D3Calendar.css';


const MONTHS_SHORT = [
    'jan', 'feb', 'mar', 'apr', 'may', 'jun',
    'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
]

const DAYS_IN_WEEK = 7
const GRID_SIZE = 12  // px
const GRID_SPACING = 2  // px

function plotMonthGrids(monthGrids) {
    var divs = monthGrids.selectAll('.month-grid')
        .data(function(d) {
            return d.values;
        })
        .enter()
        .append('div')
            .attr('class', 'month-grid')

    var svgs = divs.append('svg')
    var gs = svgs.append('g')

    gs.selectAll('rect')
        .data(function(d) {
            const OFFSET = d.values[0].date.getDay()
            for (var i = 0; i < d.values.length; i++) {
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
    var divYears = chart.selectAll('.row-year')
        .data(nestedData).enter()
        .append('div')
            .attr('id', function(d) { return 'year' + '-' + d.key })

    var yearHeading = divYears
        .append('div')
            .attr('class', 'year-heading')
        .append('h1')
            .text(function(d) { return d.key })

    var monthGrids = divYears.append('div')
        .attr('class', 'month-grid-container')

    plotMonthGrids(monthGrids)
}


/* Main */
function plot(data, el) {
    var parseTime = d3.timeParse('%Y-%m-%d')
    data.forEach(function(d) {
        d.date = parseTime(d.date)
        d.value = parseFloat(d.value)
    })


    var nestedData = d3.nest()
        .key(function(d) { return d.date.getFullYear() })
        .key(function(d) { return MONTHS_SHORT[d.date.getMonth()] } )
        .entries(data)

    plotCalendar(nestedData, el)
}

const D3Calendar = {};

D3Calendar.create = (el, data, configuration) => {
    // D3 Code to create the chart
    plot(data, el)
};

D3Calendar.update = (el, data, configuration, chart) => {
    // D3 Code to update the chart
};

D3Calendar.destroy = () => {
    // Cleaning code here
};


export default D3Calendar;
