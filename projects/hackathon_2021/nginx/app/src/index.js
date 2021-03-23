import * as d3 from 'd3';


$(document).ready(function() {
  fetch('/hack_api/test/get_data')
    .then(response => response.json())
    .then(data => createTable(data))

  fetch('http://192.168.56.101:8050/hack_api/test/get_node_map')
    .then(response => response.json())
    .then(data => {
        createChart(data, true)
        createSummaryTable(data)
    })

    registerRegenerate()
})


function registerRegenerate() {
  const handleTimeout = {
    timer_id: null,
    timer_start: null,
    pollForResult: function(resp) {
      var self = this
      if (this.timer_id === null) {
        this.timer_id = setInterval(this.fetchResult.bind(self, resp.job_id), 500)
        this.timer_start = Date.now()
      }
    },
    fetchResult: function(job_id) {
      var self = this
      fetch('/hack_api/test/generate_test_data_status/' + job_id)
        .then(response => response.text())
        .then(function(result) {
          console.log(job_id, result)
          if (result === 'finished') {
            clearInterval(self.timer_id)
            self.timer_id = null
            self.timer_start = null
            onRegenerateData()
          } else if ((Date.now() - self.timer_start) / 1000 > 2000) {
            clearInterval(self.timer_id)
            self.timer_id = null
            self.timer_start = null
          }
        })
    }
  }

  $("#regen").click(function() {
    fetch('/hack_api/test/generate_test_data')
      .then(response => response.json())
      .then(data => handleTimeout.pollForResult(data))
  })
}

function onRegenerateData() {
  fetch('/hack_api/test/get_data')
    .then(response => response.json())
    .then(data => updateTable(data))

  fetch('/hack_api/test/get_node_map')
    .then(response => response.json())
    .then(data => {
        createChart(data, false)
        updateSummaryTable(data.nodes[0])
    })
}

function updateTableGroup(groups) {
  fetch('/hack_api/test/get_data_groups', {
      headers: {
        'Content-Type': 'application/json',
      },
      method: 'POST',
      body: JSON.stringify({
        groups: groups
      })
  }).then(response => response.json())
    .then(data => updateTable(data))
}

function updateTable(data) {
  const keys = Object.keys(data[0])

  // --- remove existing table ---
  $('#dtBasicExample').DataTable().destroy()

  // --- body ---
  const tbody = d3.select('#dtBasicExample > tbody')
  const updateBody = tbody.selectAll('tr').data(data)
  const enterBody = updateBody.enter().append('tr')

  const exitBody = updateBody.exit().remove()
  const mergeBody = enterBody.merge(updateBody)

  mergeBody.selectAll('td').remove()
  keys.forEach(function(k) {
    if (k === 'rating') {
      mergeBody.append('td').html(function(d) {
        var res = ""
        const rating = +d[k]
        for (var i=0; i < rating; i++) {
          res += '<span class="fa fa-star checked"></span>'
        }
        for (var i=rating; i < 5; i++) {
          res += '<span class="far fa-star"></span>'
        }
        return res
      })
    } else {
      mergeBody.append('td').text(d => d[k])
    }
  })

  // --- create bootstrap table ---
  $('#dtBasicExample').DataTable({
    'order': [[ 1, 'asc']]
  })
}

function createTable(data) {
  if (data.length === 0) {
    return
  }

  const keys = Object.keys(data[0])

  // --- header ---
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

  updateTable(data)

  $('.dataTables_length').addClass('bs-select');
}

function createChart(data, first=false) {
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
  const height = 300
  const radius = 10

  const dataExtent = d3.extent(data.nodes, d => +d.count)
  const dataScale = d3.scaleSqrt()
    .domain([dataExtent[0], dataExtent[1]])
    .range([5, 20]);


  const links = data.links.map(d => Object.create(d));
  const nodes = data.nodes.map(d => Object.create(d));

  const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).strength(0.4))
      .force("charge", d3.forceManyBody())
      .force("center", d3.forceCenter(width / 2, height / 2).strength(0.3))
      .force("left", d3.forceY(0).strength(0.01))
      .force("right", d3.forceY(width).strength(0.01))


  if (first) {
    const svg = d3.select('#chart').append('svg')
      .attr("preserveAspectRatio", "xMinYMin meet")
      .attr('viewBox',  [0, 0, width, height])
      .attr('xmlns', 'http://www.w3.org/2000/svg')
      .classed('svg-content', true)

    const glink = svg.append("g")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .attr("class", "g-links")

    const gnode = svg.append("g")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .attr("class", "g-nodes")
  }

  const link = d3.select(".g-links").selectAll("line")
    .data(links)
    .join("line")
      .attr("stroke-width", d => dataScale(d.value));

  const node = d3.select(".g-nodes")
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
        updateAvaCountTable(data.nodes[d.index])
        updateTableGroup(data.nodes[d.index].groups)
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
  const tbodyA = tableA.append('tbody')
  const summaryData = data.nodes[0]
  updateSummaryTable(summaryData)

  const tableB = d3.select('#dtSummaryB')
  const tbodyB = tableB.append('tbody')
  const avaCount = data.nodes[0]
  updateAvaCountTable(avaCount)
}

function updateSummaryTable(summaryData) {
  var data = Object.assign({}, summaryData);
  delete data['avatar_count']
  const tbody = d3.select("#dtSummaryA > tbody")
  const keys = Object.keys(data)
  const updateBody = tbody.selectAll('tr').data(keys)
  const enterBody = updateBody.enter().append('tr')
  const exitBody = updateBody.exit().remove()
  const mergeBody = enterBody.merge(updateBody)
  mergeBody.selectAll('th').remove()
  mergeBody.selectAll('td').remove()
  mergeBody.append('th').text(d => d)
  mergeBody.append('td').text(d => data[d])
}

function updateAvaCountTable(avaCount) {
  var data = avaCount['avatar_count']
  const tbody = d3.select("#dtSummaryB > tbody")
  const keys = Object.keys(data)
  const updateBody = tbody.selectAll('tr').data(keys)
  const enterBody = updateBody.enter().append('tr')
  const exitBody = updateBody.exit().remove()
  const mergeBody = enterBody.merge(updateBody)
  mergeBody.selectAll('th').remove()
  mergeBody.selectAll('td').remove()
  mergeBody.append('th').text(d => d)
  mergeBody.append('td').text(d => data[d])
}

