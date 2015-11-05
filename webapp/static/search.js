$(function() {
    $('a#search').bind('click', function() {
      $.getJSON($SCRIPT_ROOT + '/search', {

      }, function(data) {
        $("#result").text(data.result);
      });
      return false;
    });
  });