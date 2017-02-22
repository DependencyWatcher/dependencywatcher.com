$(function($) {
	$("#scroll-to-top").click(function() {
		$("html, body").animate({ scrollTop: 0 });
	});

	$(document).scroll(function() {
		var elem = $("#navigation");
		if ($(window).scrollTop() > 500) {
			$("#scroll-to-top").fadeIn("slow");
		} else {
			$("#scroll-to-top").fadeOut("slow");
		}
	});

	$(".blog-post img").each(function() {
		var img = $(this);
		img.css({"display":"none"});
		var spinner = $("<p class=\"text-center\"><i class=\"fa fa-spinner fa-spin fa-2x\"></i></p>");
		spinner.insertAfter(img);

		function onload() {
			spinner.remove();
			img.css({"display":""});
		}

		var tempImg = new Image();
		tempImg.src = img.attr("src");
		if (tempImg.complete) {
			onload();
			tempImg.onload=function() {};
		} else {
			tempImg.onload = function() {
				onload();
				tempImg.onload=function() {};
			}
		}
	});
});
