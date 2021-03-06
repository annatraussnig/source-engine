var margin = {top: 50, right: 50, bottom: 50, left: 50},
  width = window.innerWidth - margin.left - margin.right,
  height = 750 - margin.top - margin.bottom,
  // padding between nodes
  padding = 25,
  maxRadius = 200,
  numberOfNodes = 50;

var x = d3.scale.linear()
  .domain( [-1, 1] )
  .range( [margin.left, width + margin.right ] );

// Map the basic node data to d3-friendly format.
function getNodes(data) {
  return data.map(function(node, index) {
    return {
      idealradius: node.count * 5,
      radius: 0,
      // Give each node a random color.
      color: '#fff',
      // Set the node's gravitational centerpoint.
      idealcx: x(node.avg_tweet_sentiment),
      idealcy: height / 2,
      x: x(node.avg_tweet_sentiment),
      // Add some randomization to the placement;
      // nodes stacked on the same point can produce NaN errors.
      y: height / 2 + ((Math.random() - 0.25) * (height - margin.top - margin.bottom - node.count * 5)),
      text: node.word
    };
  });
}

function getForce(nodes) {
  return d3.layout.force()
    .nodes(nodes)
    .size([width, height])
    .gravity(0)
    .charge(0.5)
    .on("tick", tick)
    .start();
}

var xAxis = d3.svg.axis()
  .scale(x);

var svg = d3.select("#sentiment")
  .append("svg:svg")
  .attr("width", width + margin.left + margin.right)
  .attr("height", height + margin.top + margin.bottom);

var loading = svg.append("text")
  .attr("x", ( width + margin.left + margin.right ) / 2)
  .attr("y", ( height + margin.top + margin.bottom ) / 2)
  .attr("dy", ".35em")
  .style("text-anchor", "middle")
  .text("Simulating. One moment please…");

/**
 * On a tick, apply custom gravity, collision detection, and node placement.
 */
function tick(e) {
  for ( i = 0; i < nodes.length; i++ ) {
    var node = nodes[i];
    /*
     * Animate the radius via the tick.
     *
     * Typically this would be performed as a transition on the SVG element itself,
     * but since this is a static force layout, we must perform it on the node.
     */
    node.radius = node.idealradius - node.idealradius * e.alpha * 10;
    node = gravity(.2 * e.alpha)(node);
    node = collide(.5)(node);
    node.cx = node.x;
    node.cy = node.y;
  }
}

/**
 * On a tick, move the node towards its desired position,
 * with a preference for accuracy of the node's x-axis placement
 * over smoothness of the clustering, which would produce inaccurate data presentation.
 */
function gravity(alpha) {
  return function(d) {
    d.y += (d.idealcy - d.y) * alpha;
    d.x += (d.idealcx - d.x) * alpha * 3;
    return d;
  };
}

/**
 * On a tick, resolve collisions between nodes.
 */
function collide(alpha) {
  var quadtree = d3.geom.quadtree(nodes);
  return function(d) {
    var r = d.radius + maxRadius + padding,
      nx1 = d.x - r,
      nx2 = d.x + r,
      ny1 = d.y - r,
      ny2 = d.y + r;
    quadtree.visit(function(quad, x1, y1, x2, y2) {
      if (quad.point && (quad.point !== d)) {
        var x = d.x - quad.point.x,
          y = d.y - quad.point.y,
          l = Math.sqrt(x * x + y * y),
          r = d.radius + quad.point.radius + padding;
        if (l < r) {
          l = (l - r) / l * alpha;
          d.x -= x *= l;
          d.y -= y *= l;
          quad.point.x += x;
          quad.point.y += y;
        }
      }
      return x1 > nx2 || x2 < nx1 || y1 > ny2 || y2 < ny1;
    });
    return d;
  };
}

/**
 * Run the force layout to compute where each node should be placed,
 * then replace the loading text with the graph.
 */
var nodes

function renderGraph(data) {
  if(!data)
  {
    return
  }
  // Run the layout a fixed number of times.
  // The ideal number of times scales with graph complexity.
  // Of course, don't run too long—you'll hang the page!
  nodes = getNodes(data.words)
  var force = getForce(nodes)

  force.start();
  for (var i = 10; i > 0; --i) force.tick();
  force.stop();

  var elem = svg.selectAll("g myCircleText")
    .data(nodes)

  /*Create and place the "blocks" containing the circle and the text */
  var elemEnter = elem.enter()
    .append("g")
    .attr("transform", function(d){return "translate("+d.x+","+d.y+")"})

  /*Create the circle for each block */
  var circle = elemEnter.append("circle")
    .style("fill", function(d) { return "#FF8C00"; })
    .attr("r", function(d){return d.radius} )

  /* Create the text for each block */
  elemEnter.append("text")
    .attr("text-anchor", "middle")
    .attr("fill", "#fff")
    .text(function(d){return d.text})

  loading.remove();
}
