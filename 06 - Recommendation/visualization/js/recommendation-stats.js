var loadStats = function(option) {

    var groups_svg = d3.select("#" + option + "-content-row .groups");
    var groups_data = [];

    for (var i = 0; i < dataset.sizes[option]; i++) {
        groups_data.push({
            size : 0,
            outlets : [],
            id : i
        });
    };

    $.each(dataset.outlets, function(idx, outlet) {
        groups_data[dataset.communities[outlet][option]].size++;
        groups_data[dataset.communities[outlet][option]].outlets.push(outlet);
    });

    var svg = d3.select("#" + option + "-content-row .groups");
    createPie(svg, groups_data, option);

    
    var user_data = [];

    for (var i = 0; i < dataset.sizes[option]; i++) {
        user_data.push({
            size : 0,
            outlets : [],
            id : i
        });
    };

    $.each(dataset.followed_outlets, function(idx, outlet) {
        user_data[dataset.communities[outlet][option]].size++;
        user_data[dataset.communities[outlet][option]].outlets.push(outlet);
    });

    var user_svg = d3.select("#" + option + "-content-row .user-consumption");
    createPie(user_svg, user_data, option);

    $("#" + option + "-title-row").removeClass("hidden");
    $("#" + option + "-text-row").removeClass("hidden");
    $("#" + option + "-content-row").removeClass("hidden");
    $("#" + option + "-graph-row").removeClass("hidden");
    
}

var createPie = function(svg, data, option) {
    svg.empty();
    var width = 200;
        height = 200;
        radius = Math.min(width, height) / 2;

    var color = d3.scale.category20();
    var arc = d3.svg.arc()
        .outerRadius(radius - 10)
        .innerRadius(radius - 50);

    var pie = d3.layout.pie()
        .sort(null)
        .value(function(d) { return d.size; });

    var g = svg.append("g")
        .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")")
        .selectAll(".arc")
        .data(pie(data))
        .enter().append("g")
        .attr("class", "arc");


    var tooltip = $("div.tooltip");

    var total  = 0;
    $.each(data, function(idx, obj) {
        total += obj.size;
    });

    //I want to force colors to be assigned in this order.
    color(1);
    color(0);

    for (var i = 2; i < dataset.sizes[option]; i++) {
        color(i);
    }

    g.append("path")
        .attr("d", arc)
        .style("fill", function(d) { return color(d.data.id); })
        .on("mouseover", function(d) {
            var percent = Math.round(1000 * d.data.size / total ) / 10;
            tooltip.find('.title').html((d.data.id === 0)? "Other outlets" :
                    "Group " + d.data.id);
            tooltip.find('.size').html(d.data.size + " outlets (" + percent + '%)'); 
        tooltip.css('display', 'block');   })
        .on('mouseout', function() {
            tooltip.css('display', 'none');
        })
        .on('mousemove', function(d) {
            tooltip
                .css('top',  (d3.event.pageY + 10) + 'px')
                .css('left', (d3.event.pageX + 10) + 'px');
        });

};

