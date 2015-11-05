$(function() {
    $('a#search').bind('click', function() {

        var fd = new FormData();
        var file_data = $('input[type="file"]')[0].files; // for multiple files
        fd.append("file", file_data[0]);

        $.ajax({
            url: $SCRIPT_ROOT + '/search',
            processData: false,
            contentType: false,
            method: 'POST',
            data: fd
        }).done(function(data) {
            $("#result").text(data.result);
        });
        return false;
    });
  });