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

	$('.listing').on('click', '.control', function() {
        if($(this).hasClass('play')) {
            $(this).parent().find('audio').trigger('play')
			var oThis = this
			$(this).parent().find('audio').one('ended', function() {
				$(oThis).toggleClass('pause play')
			})
        }
        else {
            $(this).parent().find('audio').trigger('pause')
        }
        $(this).toggleClass('pause play');
	});


})

function getAcceptedFiles() {
	return ".mp3,.wav";
}

function parseResults(result){
	var name, artist, url, rating, similarity, orig_file, orig_url;
	var results = result["results"]

	$.each(results, function(index, value){
		name = value["name"];
		url = value["audio_url"];
        similarity = value["similarity"];
		renderResult(name, url, similarity);
	});

	$('#original-file-name').html(result["original_file"])
	$('.listing audio').attr('src', result["original_audio_url"])

	$('.upload-form').fadeOut(function(){
		$('.listing').fadeIn();
	})
}


function renderResult(name, url, similarity){
	var audio = '<audio><source src="' + url + '"/></audio>'
	var play_button = '<div class="control play"><span class="left"></span><span class="right"></span></div>'
	var link = '<a href="' + url + '">' + name + '</a>';
	var star = '<span class="star">' + similarity + '</span>';
	var starWrapper = '<div class="star-wrapper">' + star + '</div>';
	var html = '<li>' + '<span class="audio-elements">' + audio + play_button + '</span>' + link + starWrapper + '</li>';

	$('#result-listing').append(html);
}
