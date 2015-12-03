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

		parseResults(response["result"]);

	})

	$('.listing').on('click', '.control', function() {
        if($(this).hasClass('play')) {
            $(this).parent().find('audio').trigger('play')
        }
        else {
            $(this).parent().find('audio').trigger('pause')
        }
        $(this).toggleClass('pause play');
	});

    $('.listing').on('ended', 'audio', function() {
        $(this).parent().find('.control').removeClass('pause')
        $(this).parent().find('.control').addClass('play')
    })


})

function getAcceptedFiles() {
	return ".mp3,.wav";
}

function parseResults(results){
	var name, artist, url, rating, similarity, orig_file, orig_url;

	$.each(results, function(index, value){
		name = value["name"];
		url = value["audio_url"];
        similarity = value["similarity"];
        orig_file = value["original_file"];
        orig_url = value["original_audio_url"];
		renderResult(name, url, similarity, orig_file, orig_url);
	});

	setRatingValue();
	$('.upload-form').fadeOut(function(){
		$('.listing').fadeIn();
	})
}

function ended() {
    alert("THE END!")
}


function renderResult(name, url, similarity, orig_file, orig_url){
	var audio = '<audio onended="ended()"><source src="' + url + '"/></audio>'
	var play_button = '<div class="control play"><span class="left"></span><span class="right"></span></div>'
	var link = '<a href="' + url + '">' + name + '</a>';
	var star = '<span class="star"></span>';
	var starWrapper = '<div class="star-wrapper">' + star + '</div>';
	var html = '<li>' + '<span class="audio-elements">' +audio + play_button + '</span>' + link + starWrapper + '</li>';

	$('#result-listing').append(html);
    $('#original-file-info span').html(orig_file)
}

function setRatingValue(){
	$('.listing .star-bg').each(function(){
		var rating = parseInt($(this).attr('data-rate')) * 0.36;
		$(this).css('height', rating + 'px');
	})
}