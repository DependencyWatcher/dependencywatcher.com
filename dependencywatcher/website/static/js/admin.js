$(function($) {
	$.getUrlParam = function(name) {
		var vars = window.location.search.substring(1).split("&");
		for (var i = 0; i < vars.length; i++) {
			var param = vars[i].split("=");
			if (param[0] == name) {
				return param[1];
			}
		}
	}      

	$("#navigation").on("mouseover", ".navbar-nav>li>a", function() {
		if ($("#navigation .navbar-nav>.open").length > 0) {
			$("#navigation .navbar-nav>li").removeClass("open");
			$(this).parent().addClass("open");
		}
	});

	$("[data-toggle='tooltip']").tooltip({
		animated : "fade",
		container: "body"
	});

	$(".repo-url").click(function() {
		document.location.href = "/repository/" + encodeURIComponent($(this).data("url"));
	});

	function switchButton(btnGroup) {
		var input = btnGroup.closest(".form-group").find("input:checkbox");
		btnGroup.find(".btn").each(function() {
			$(this).toggleClass("active btn-default btn-primary");
			if ($(this).hasClass("active")) {
				if ($(this).text() == "ON") {
					input.prop("checked", true);
				} else {
					input.prop("checked", false);
				}
				input.trigger("change");
			}
		});
	}
	$(".btn-toggle .btn").click(function() {
		switchButton($(this).closest(".btn-toggle"));
	});
	
	$("input:checkbox").each(function() {
		if (!$(this).is(":checked")) {
			switchButton($(this).closest(".form-group").find(".btn-toggle"));
		}
	});
});
