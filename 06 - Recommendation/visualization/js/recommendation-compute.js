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

    dataset.original_target_set = new Set(target_set);


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


