import * as d3 from 'd3';


$(document).ready(function() {
  fetch('http://192.168.56.101:8050/hack_api/test/get_data')
    .then(response => response.json())
    .then(data => createTable(data))

  fetch('http://192.168.56.101:8050/hack_api/test/get_node_map')
    .then(response => response.json())
    .then(data => {
        createChart(data)
        createSummaryTable(data)
    })
})

function updateTable(groups) {
  fetch('http://192.168.56.101:8050/hack_api/test/get_data')
}

function createTable(data) {
  if (data.length === 0) {
    return
  }

  // --- header ---
  const keys = Object.keys(data[0])
  const thead = d3.select('#dtBasicExample').append('thead')
  const theadrow = thead.append('tr')
  const updateHead = theadrow.selectAll('th').data(keys)
  const enterHead = updateHead.enter().append('th')
  const exitHead = updateHead.exit().remove()
  const mergeHead = enterHead.merge(updateHead)
    .attr('class', 'th-sm')
    .text(d => d)

  // --- body ---
  const tbody = d3.select('#dtBasicExample').append('tbody')
  const updateBody = tbody.selectAll('tr').data(data)
  const enterBody = updateBody.enter().append('tr')
  const exitBody = updateBody.exit().remove()
  const mergeBody = enterBody.merge(updateBody)

  keys.forEach(k => mergeBody.append('td').text(d => d[k]))

  // --- create bootstrap table ---
  $('#dtBasicExample').DataTable();
  $('.dataTables_length').addClass('bs-select');
}

function createChart(data) {
  const drag = function(simulation) {
    
    function dragstarted(event) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }
    
    function dragged(event) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }
    
    function dragended(event) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }
    
    return d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
  }

  const width = 600
  const height = 400
  const radius = 5

  const dataExtent = d3.extent(data.nodes, d => +d.count)
  const dataScale = d3.scaleSqrt()
    .domain([dataExtent[0], dataExtent[1]])
    .range([5, 20]);

  console.log(dataExtent)

  const links = data.links.map(d => Object.create(d));
  const nodes = data.nodes.map(d => Object.create(d));

  const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).strength(0.4))
      .force("charge", d3.forceManyBody())
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("left", d3.forceY(0).strength(0.01))
      .force("right", d3.forceY(width).strength(0.01))


  const svg = d3.select('#chart').append('svg')
    .attr("preserveAspectRatio", "xMinYMin meet")
    .attr('viewBox',  [0, 0, width, height])
    .classed('svg-content', true)

  const link = svg.append("g")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
    .selectAll("line")
    .data(links)
    .join("line")
      .attr("stroke-width", d => dataScale(d.value));

  const node = svg.append("g")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .attr("class", "g-nodes")
    .selectAll("circle")
    .data(nodes)
    .join("circle")
      .attr("r", d => dataScale(d.count))
      .attr("fill", 'LightSteelBlue')
      .on("click", function(e, d) {
        const elems = d3.selectAll('.g-nodes > circle').attr('fill', 'LightSteelBlue')
        d3.select(e.currentTarget).attr('fill', 'steelblue')
        for (var i=0; i < data.nodes.length; i++) {
            const issubset = data.nodes[i].groups.every(function(val) {
              return data.nodes[d.index].groups.indexOf(val) >= 0;
            })
            if (issubset) {
              d3.select(elems.nodes()[i]).attr('fill', 'steelblue')
            }
        }
        updateSummaryTable(data.nodes[d.index])
      })
      .call(drag(simulation));

  simulation.on("tick", () => {
    link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

    node
        .attr("cx", function(d) { return d.x = Math.max(radius, Math.min(width - radius, d.x)); })
        .attr("cy", function(d) { return d.y = Math.max(radius, Math.min(height - radius, d.y)); });
  });
}

function createSummaryTable(data) {
  const tableA = d3.select('#dtSummaryA')
  const tbody = tableA.append('tbody')
  const summaryData = data.nodes[0]
  updateSummaryTable(summaryData)
}

function updateSummaryTable(summaryData) {
  const tbody = d3.select("#dtSummaryA > tbody")
  const keys = Object.keys(summaryData)
  const updateBody = tbody.selectAll('tr').data(keys)
  const enterBody = updateBody.enter().append('tr')
  const exitBody = updateBody.exit().remove()
  const mergeBody = enterBody.merge(updateBody)
  mergeBody.selectAll('th').remove()
  mergeBody.selectAll('td').remove()
  mergeBody.append('th').text(d => d)
  mergeBody.append('td').text(d => summaryData[d])
}
