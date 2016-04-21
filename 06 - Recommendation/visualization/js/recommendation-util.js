
var formatList = function(items_list) {
    var str_list = items_list.join(", ");
    var n = str_list.lastIndexOf(", ");
    if (n >= 0) {
        return str_list.substring(0, n) + " and " + str_list.substring(n + 2);
    } else {
        return str_list;
    }
}


var getRandomShufle = function(array) {
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
};


