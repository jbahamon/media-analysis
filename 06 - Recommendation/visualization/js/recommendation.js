var dataset = {};

/////////////////////////////////////////////////////////////////////////////////
// EVENTS AND LIBRARY SETUP /////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
//
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

    $.each(dataset.labels, function(idx, label) {
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

        var button = $("#randomize");
        
        getUserData( function() {
        selectOptions();
        var recommendations = getRecommendations();
        var results_list = $("#results");
        results_list.empty();

        $.each(recommendations, function(idx, outlet) {
           results_list
               .append($("<li>")
               .append($("<a>")
                   .attr("href", "https://www.twitter.com/intent/user?screen_name=" + outlet)
                   .attr("target", "_blank")
                   .attr("class", "recommendation-link")
               .append($("<span>").attr("class", "suggestion")
               .text("@" + outlet))));
        });
        $("#results-row").removeClass("hidden");
        } );
    }
});
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

    $.getJSON("http://localhost:5000/screen_name/" + screen_name, function(following_list) {
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
            target_set.add(i + total)
        }

        dataset.offsets[option] = total;
        total += dataset.sizes[option];
    });

    dataset.target_set = target_set;

};


/////////////////////////////////////////////////////////////////////////////////
// RECOMMENDATION GENERATION/////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////

var getRecommendations = function() {
    var target_set = dataset.target_set;

    $.each(dataset.followed_outlets, function(_, outlet) {
        $.each(dataset.selected_options, function(__, option) {
            target_set.delete(
                dataset.communities[outlet][option] + dataset.offsets[option]
            );
        });
    });

    //we copy the outlet names
    var available_outlets = dataset.outlets.slice(0);
    var recommendations = [];
    var new_recommendation;

    var available_outlets = dataset.outlets.slice(0);
    var scores = {};

    $.each(available_outlets, function(idx, outlet) {
        scores[outlet] = 0;
    });

    var i = 0; 
    while (target_set.size > 0) {
        /* begin draft code */
        $.each(scores, function(outlet, old_score) {
            scores[outlet] = 0;

            $.each(dataset.selected_options, function(idx2, option) {
                var group = dataset.communities[outlet][option] +
                        dataset.offsets[option];

                if (target_set.has(group))
                    scores[outlet]++;
            });

            if (scores[outlet] === 0) {
                delete scores[outlet]; 
            }
        });

        available_outlets = Object.keys(scores);
        var random_indices = getRandomShufle(available_outlets);

        available_outlets.sort(function(a, b) {
            if (scores[a] === scores[b]) {
                return random_indices[a] - random_indices[b];
            } else {
                return scores[b] - scores[a];
            }
        });

        new_recommendation = available_outlets.shift();
        
        if (new_recommendation === undefined || scores[new_recommendation] === 0) {
            console.error("No options left for covering all diversity choices." +
                    "Something might be wrong.");
            break;
        }

        $.each(dataset.selected_options, function(idx, option) {
            target_set.delete(dataset.communities[new_recommendation][option] +
                    dataset.offsets[option]);
        });
        recommendations.push(new_recommendation);
    }

    return recommendations;
};


function getRandomShufle(array) {
  var currentIndex = array.length, temporaryValue, randomIndex;

  // While there remain elements to shuffle...
  while (0 !== currentIndex) {

    // Pick a remaining element...
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex -= 1;

    // And swap it with the current element.
    temporaryValue = array[currentIndex];
    array[currentIndex] = array[randomIndex];
    array[randomIndex] = temporaryValue;
  }

  var random_indices = {}

  $.each(random_indices, function(idx, val) {
    random_indices[val] = idx;
  });

  return random_indices;
}


