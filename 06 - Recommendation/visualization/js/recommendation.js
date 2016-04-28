var dataset = {};

/////////////////////////////////////////////////////////////////////////////////
// EVENTS AND LIBRARY SETUP /////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////

$.validator.setDefaults({
    errorElement: "span",
    errorClass: "help-block",
    highlight: function (element, errorClass, validClass) {
        $(element).closest('.form-group').addClass('has-error');
    },
    unhighlight: function (element, errorClass, validClass) {
        $(element).closest('.form-group').removeClass('has-error');
    },
    errorPlacement: function (error, element) {
        if (element.prop('type') === 'checkbox' && element.parent().is("label")) {
            error.insertAfter(element.parent().parent());
        } else if (element.parent('.input-group').length || element.prop('type')
                === 'checkbox' || element.prop('type') === 'radio') {
            error.insertAfter(element.parent());
        } else {
            error.insertAfter(element);
        }
    }
});

$.validator.addMethod('twitterusername', function (value) { 
        return /^[_A-z0-9]{1,}$/.test(value); 
}, 'Please enter a valid Twitter screen name.');

/////////////////////////////////////////////////////////////////////////////////
// DATA SETUP ///////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
    
$.getJSON("community_sets.json", function(sets) {
    dataset = sets;
    dataset.offsets = {};
    dataset.username = "";

    var checkbox_group = $("#options");
    var title_template = $("#template-title-row");
    var text_template = $("#template-text-row");
    var content_template = $("#template-content-row");
    var graph_template = $("#template-graph-row");


    var total = 0;

    $.each(dataset.labels, function(idx, label) {

        dataset.offsets[label] = total;
        total += dataset.sizes[label];
 
        $("<label>")
        .attr("class", "btn btn-primary")
            .append($("<input />",
                { "type"  : "checkbox",
                  "value" : label,
                  "autocomplete": "off",
                  "name"  : "option",
                }))
            .append(label)
        .appendTo(checkbox_group);

        var new_title = title_template.clone();
        new_title.find(".title").text(label + " Analysis");
        new_title.attr("id", label + "-title-row");

        var new_text = text_template.clone();
        new_text.find(".n").text(dataset.sizes[label]);
        new_text.find(".criterion").text(label.toLowerCase() + "-based");
        new_text.attr("id", label + "-text-row");

        var new_content = content_template.clone();
        new_content.attr("id", label + "-content-row");

        var new_graph = graph_template.clone();
        new_graph.attr("id", label + "-graph-row");

        new_graph.find("#template-heading").attr("id", label + "-heading");
        new_graph.find("a")
            .attr("href", "#" + label + "-panel")
            .attr("aria-controls", label + "-panel");

        new_graph.find("#template-panel")
            .attr("id", label + "-panel")
            .attr("aria-labelledby", label + "-heading");

        new_title.insertBefore(title_template);
        new_text.insertBefore(title_template);
        new_content.insertBefore(title_template);
        new_graph.insertBefore(title_template);

        var panel      = new_graph.find(".panel-body");
        var graph_svg  = new_graph.find(".graph-svg");
        var force;

        if (dataset.graphs[label].words !== undefined) {
            force = createGraph(d3.selectAll(graph_svg),
                    300,
                    300,
                    dataset.graphs[label]);
        } else {
            panel.find(".cloud-svg").remove();

            force = createGraph(d3.selectAll(graph_svg),
                    400,
                    400,
                    dataset.graphs[label]);
        }

        new_graph.find(".panel-collapse").on("show.bs.collapse", function () {
            force.start();
        }).bind("hide.bs.collapse", function () {
            force.stop();
        });
    });
});

$().ready(function() {

$("#user-form").validate({
    debug: true,
    rules: {
        username: {
            required: true,
            minlength: 1,
            maxlength: 15,
            twitterusername: true
        },
        option: {
            required: true
        }
    },
    submitHandler: function() {

        var button = $(".randomize");

        button.attr("disabled", true); 
        button.html('<span class="glyphicon glyphicon-refresh spinning"></span> Loading...');
        getUserData( function() {
        selectOptions();

        $(".option-title").addClass("hidden");
        $(".option-graph").addClass("hidden");
        $(".option-content").addClass("hidden");

        $.each(dataset.selected_options, function(idx, val) {
            loadStats(val);
        });

        var recommendations = getRecommendations();
        var results_list = $("#results");
        results_list.empty();

        $.each(recommendations, function(idx, outlet) {
            options_list = [];
            $.each(dataset.selected_options, function(idx, option) {
                if (dataset.original_target_set.has(
                            dataset.communities[outlet][option] +
                            dataset.offsets[option]))
                    options_list.push(option.toLowerCase());
            });


           results_list
               .append($("<li>")
               .append($("<a>")
                   .attr("href", "https://www.twitter.com/intent/user?screen_name=" + outlet)
                   .attr("target", "_blank")
                   .attr("class", "recommendation-link")
               .append($("<span>")
                   .attr("class", "suggestion")
                   .text("@" + outlet)))
               .append($("<span>")
                   .text(" (helps with "+ formatList(options_list) +" diversity)")));
        });

        $("#results-row").removeClass("hidden");
        button.attr("disabled", false); 
        $("#try").html("Try it!");
        $("#again").html("Try again!");

        } );
    }
});

$("#again").on("click", function() { $("#user-form").submit() });

});

/////////////////////////////////////////////////////////////////////////////////
// PARAMETER READING ////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
var getUserData = function(after_done) {
    var screen_name = $("#username").val().toLowerCase();

    if (dataset.screen_name === screen_name) {
        after_done();
        return;
    }
    
    dataset.screen_name = screen_name;

//    $.getJSON("http://localhost:5000/screen_name/" + screen_name, function(following_list) {
    $.getJSON("./following.json", function(following_list) {
        dataset.followed_outlets = [];

        $.each(following_list, function(idx, outlet_id) {

            if (dataset.ids[outlet_id.toString()] !== undefined)
                dataset.followed_outlets.push(dataset.ids[outlet_id.toString()]);
        });

        after_done();
    });
}


var selectOptions = function() {
    dataset.selected_options = [];
    $("input:checked").each(function() {
        dataset.selected_options.push($(this).attr("value"));
    });

    var total = 0;
    var target_set = new Set();

    $.each(dataset.selected_options, function(idx, option) {
        
        // We start from 1 as the first cluster is the 'unclustered elements'
        // one.
        for (var i = 1; i < dataset.sizes[option]; i++) {
            target_set.add(i + dataset.offsets[option])
        }
    });

    dataset.target_set = target_set;

};

