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

})

function getAcceptedFiles() {
	return ".mp3,.wav";
}

function parseResults(results){
	var name, artist, url, rating, similarity;

	$.each(results, function(index, value){
		name = value["name"];
		url = value["audio_url"];
        similarity = value["similarity"];
		renderResult(name, url, rating, similarity);
	});

	setRatingValue();
	$('.upload-form').fadeOut(function(){
		$('.listing').fadeIn();
	})
}

function renderResult(name, url, similarity){
	var audio = '<audio controls><source src="' + url + '"/></audio>'
	var link = '<a href="' + url + '">' + name + '</a>';
	var star = '<span class="star"></span>';
	var starWrapper = '<div class="star-wrapper">' + star + '</div>';
	var html = '<li>' + audio + link + starWrapper + '</li>';

	$('#result-listing').append(html);
}

function setRatingValue(){
	$('.listing .star-bg').each(function(){
		var rating = parseInt($(this).attr('data-rate')) * 0.36;
		$(this).css('height', rating + 'px');
	})
}