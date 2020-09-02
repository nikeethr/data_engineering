var BOX_WIDTH_PX = 15
var DAYS_PER_WEEK = 7
var WEEKS_PER_MONTH = 5  // or 4
var BOX_PADDING = 2
// var MARGIN = {
//   l: 10, r: 10, b:10, t:10
// }

var WIDTH_PX = BOX_WIDTH_PX * WEEKS_PER_MONTH
var HEIGHT_PX = BOX_WIDTH_PX * DAYS_PER_WEEK

var matrix = [
  [ 0,  1,  2,  3, 20, 15, 0],
  [ 4,  5,  6,  0, 0, 0, 1],
  [ 8,  9, 0, 11, 2, 8, 5],
  [12, 13, 14, 15, 1, 5, 10],
];

function plotMonthlyGrids(id) {
  var container = d3.select(id).append('div')

  monthContainer = container.append('div')
    .attr('class', 'month-text')
    .text('JAN')
  boxContainer = container.append('div')

  var svg = boxContainer.append('svg')
    .attr('width', WIDTH_PX)
    .attr('height', HEIGHT_PX)

  var gBox = svg.append('g')

  var gRow = gBox.selectAll('.grow')
    .data(matrix).enter()
    .append('g')
    .attr('transform', function(d, i) {
      return 'translate(' + i * (BOX_WIDTH_PX + BOX_PADDING)  + ',0)'
    })

  var gRect = gRow.selectAll('rect')
    .data(function(d, i) { return d })

  gRect.enter()
    .append('rect')
    .attr('y', function(d, i) {return i * (BOX_WIDTH_PX + BOX_PADDING)})
    .attr('width', BOX_WIDTH_PX)
    .attr('height', BOX_WIDTH_PX)
    .attr('fill', function(d, i) {
      if (d == 0) return 'darkgrey'
      else return d3.interpolateReds(d/30)
    })

  var bbox = gBox.node().getBBox()

  svg
    .attr('width', bbox.width)
    .attr('height', bbox.height)
}


function drawYearHeader() {
}

function drawYearlyPanels(data) {
  d3.select('#chart')
    .selectAll('.panel')
    .data(data).enter().append()
}

var parseDate = d3.timeParse('%Y-%m-%d');

d3.csv('/data/data.csv').then(function(d) {
  d.forEach(function(d) { d.date = parseDate(d.date) })

  var nested_data = d3.nest()
    .key(function(d) { return d.date.getFullYear() })
    .key(function(d) { return d.date.getMonth() })
    .entries(d)

})
