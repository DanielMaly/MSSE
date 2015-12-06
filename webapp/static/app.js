var myDropzone;

$(document).ready(function () {

    myDropzone = new Dropzone("#dropzone", {
        url: $SCRIPT_ROOT + '/search',
        uploadMultiple: false,
        //acceptedFiles: getAcceptedFiles()
    });

    myDropzone.on("addedfile", function (file) {
        $('#dropzone').addClass('processing')
    });
    myDropzone.on("addedfile", function () {
        //When file is added
    })
    myDropzone.on("success", function (file, response) {
        //console.log(file);

        parseResults(response);

    })
    myDropzone.on("sending", function(file, xhr, formData) {
        formData.append("dataset", $("#dataset").val())
        formData.append("engine", $("#engine").val())
    })

    $('.listing').on('click', '.control', function () {
        if ($(this).hasClass('play')) {
            $(this).parent().find('audio').trigger('play')
            var oThis = this
            $(this).parent().find('audio').one('ended', function () {
                $(oThis).toggleClass('pause play')
            })
        }
        else {
            $(this).parent().find('audio').trigger('pause')
        }
        $(this).toggleClass('pause play');
    });


    $(".custom-select").each(function () {
        var classes = $(this).attr("class"),
            id = $(this).attr("id"),
            name = $(this).attr("name");
        var template = '<div class="' + classes + '">';
        template += '<span class="custom-select-trigger">' + $(this).attr("placeholder") + '</span>';
        template += '<div class="custom-options">';
        $(this).find("option").each(function () {
            template += '<span class="custom-option ' + $(this).attr("class") + '" data-value="' + $(this).attr("value") + '">' + $(this).html() + '</span>';
        });
        template += '</div></div>';

        $(this).wrap('<div class="custom-select-wrapper"></div>');
        $(this).hide();
        $(this).after(template);
    });
    $(".custom-option:first-of-type").hover(function () {
        $(this).parents(".custom-options").addClass("option-hover");
    }, function () {
        $(this).parents(".custom-options").removeClass("option-hover");
    });
    $(".custom-select-trigger").on("click", function () {
        $('html').one('click', function () {
            $(".custom-select").removeClass("opened");
        });
        $(this).parents(".custom-select").toggleClass("opened");
        event.stopPropagation();
    });
    $(".custom-option").on("click", function () {
        $(this).parents(".custom-select-wrapper").find("select").val($(this).data("value"));
        $(this).parents(".custom-options").find(".custom-option").removeClass("selection");
        $(this).addClass("selection");
        $(this).parents(".custom-select").removeClass("opened");
        $(this).parents(".custom-select").find(".custom-select-trigger").text($(this).text());
    });


})

function getAcceptedFiles() {
    return ".mp3,.wav";
}

function parseResults(result) {
    var name, artist, url, rating, similarity, orig_file, orig_url;
    var results = result["results"]

    $.each(results, function (index, value) {
        name = value["name"];
        url = value["audio_url"];
        similarity = value["similarity"];
        renderResult(name, url, similarity);
    });

    $('#original-file-name').html(result["original_file"])
    $('.original-file audio').attr('src', result["original_audio_url"])

    $('.upload-form').fadeOut(function () {
        $('.listing').fadeIn();
    })
}


function renderResult(name, url, similarity) {
    var audio = '<audio><source src="' + url + '"/></audio>'
    var play_button = '<div class="control play"><span class="left"></span><span class="right"></span></div>'
    var link = '<a href="' + url + '">' + name + '</a>';
    var star = '<span class="star">' + similarity + '</span>';
    var starWrapper = '<div class="star-wrapper">' + star + '</div>';
    var html = '<li>' + '<span class="audio-elements">' + audio + play_button + '</span>' + link + starWrapper + '</li>';

    $('#result-listing').append(html);
}
