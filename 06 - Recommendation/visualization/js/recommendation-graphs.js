var createGraph =  function(svg, width, height, graph) {
    /* Scales setup */
    var sizes = $.map(graph.nodes, function(n) { return n.size });

    var max_size = Math.max.apply( Math, sizes);
    var min_size = Math.min.apply( Math, sizes);
    
    var linkcolorpos = d3.scale.linear()
        .domain([0,1])
        .range(["gray", "red"]);

    var size = d3.scale.log()
        .domain([1000, max_size])
        .range([3, 20])
        .clamp([true, false]);

    var color = d3.scale.category20();
    color(1);
    color(0);

    for (var i = 2; i < 20; i++) {
        color(i);
    }

    /* SVG shenanigans start here */
    svg.attr("width", width)
       .attr("height", height)
       .attr("viewBox", "0 0 400 400")
       .attr("preserveAspectRatio", "xMidYMid meet");

    /* The force engine */
    var force = d3.layout.force()
        .charge(-100)
        .gravity(0.2)
        .linkDistance(60)
        .size([400, 400])
        .nodes(graph.nodes)
        .links(graph.links);
 
    var linksvg = svg.append("svg:g");
    var link = linksvg.selectAll(".link")
        .data(graph.links)
        .enter()
        .append("line", ".node")
        .attr("class", "link")
        .style("stroke", function(d) { return linkcolorpos(d.value);});

    link.append("title")
        .text(function(d)  { return "Similarity " + 
            d.source.name + " - " + d.target.name + ": " + d.value; });

    var node = svg.selectAll(".node")
        .data(graph.nodes, function(d) { return d.index; })
        .enter().append("circle")
        .attr("class", function (d) { return "node " + d.index; })
        .attr("r", function(d) { return size(d.size); })
        .style("fill", function(d) { return color(d.color_value); })
        .call(force.drag);

    node.insert("title")
        .text(function(d) { 
            return d.name + " " + 
                ((d.color_value === 0)? "(Other outlets)": "(Group " + d.color_value + ")");
        });

    force
        .on("tick", function() {
            link.attr("x1", function(d) { return d.source.x; })
                .attr("y1", function(d) { return d.source.y; })
                .attr("x2", function(d) { return d.target.x; })
                .attr("y2", function(d) { return d.target.y; });

            node.attr("cx", function(d) { return d.x; })
                .attr("cy", function(d) { return d.y; });
        })

    if (graph.words !== undefined ) {
        var cloud_svg = d3.select(svg.node().previousElementSibling);

        var cloud_layout = createCloud(cloud_svg, graph.words, 300,300);
        node
            .on("click", function(clicked) {
                node.style("stroke-width", 
                        function(d) { return (d.color_value === clicked.color_value)? 3 : 1; })
                    .call(force.drag);
                force.start();
                updateCloud(graph.words, clicked.color_value, cloud_layout);
            });
    }

    return force;

}


var drawWords = function(svg, words, width, height) {
    var color = d3.scale.category20b();
    svg.selectAll("g").remove();
    svg.append("g")
        .attr("transform", "translate(" + width/2 + "," + height/2 + ")")
        .selectAll("text")
        .data(words)
        .enter().append("text")
        .style("font-size", function(d) { return d.size + "px"; })
        .style("font-family", "Impact")
        .style("fill", function(d, i) { return color(i) })
        .attr("text-anchor", "middle")
        .attr("transform", function(d) {
            return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
        })
        .text(function(d) { return d.text; });
}

var updateCloud = function(words, community, cloud_layout){
    var textsize = d3.scale.linear()
        .domain([0,1])
        .range([20,60]);
    var community_words = [];

    $.each(words[(community) + ""],
            function(key, value) {
                community_words.push({
                    "text": key,
                    "size": value
                })});
    cloud_layout
        .words(community_words)
        .padding(5)
        .rotate(0)
        .font("Impact")
        .fontSize(function(d) { return textsize(d.size); })
        .start();
}

var createCloud = function(svg, words, width, height) {

       var cloud_layout = d3.layout.cloud()
        .size([width,height])
        .padding(5)
        .rotate(0)
        .font("Impact")
        .on("end", function(words) {
            drawWords(svg, words, width, height);
        })
        .start();
    return cloud_layout;
}

