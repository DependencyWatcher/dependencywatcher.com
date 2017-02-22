#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from flask import render_template, redirect, url_for, request, abort
from dependencywatcher.website.webapp import app, db
from dependencywatcher.website.model import BlogPost, Tag, get_or_create
from dependencywatcher.website.forms import BlogPostForm
from flask.ext.login import current_user, login_required

@app.route("/blog/<slug>", methods=["GET"])
def blog_post_by_slug(slug):
	post = BlogPost.query.filter_by(slug=slug).first()
	if post is None:
		abort(404)
	return render_template("blog.html", posts=[post], title=post.title)

@app.route("/blog", methods=["GET"])
@app.route("/blog/<int:page>", methods=["GET"])
def blog(page=1):
	posts = BlogPost.query.order_by(BlogPost.date.desc()).paginate(page=page, per_page=3)
	return render_template("blog.html", posts=posts.items)

@app.route("/blog/tag/<tag>", methods=["GET"])
@app.route("/blog/tag/<tag>/<int:page>", methods=["GET"])
def blog_by_tag(tag, page=1):
	posts = BlogPost.query.filter(BlogPost.tags.any(name=tag)).paginate(page=page, per_page=3)
	return render_template("blog.html", posts=posts.items)

@app.route("/blog/post", methods=["GET", "POST"])
@login_required
def blog_post():
	if current_user.has_roles("editor"):
		form = BlogPostForm(request.form)
		if form.validate_on_submit():
			post = BlogPost()
			form.populate_obj(post)
			post.author = current_user.email
			post.make_slug()
			db.session.add(post)
			for tag_name in request.form.getlist("tags"):
				post.tags.append(get_or_create(Tag, name=tag_name))
			db.session.commit()
			return redirect(url_for("blog"))
		return render_template("blog_post.html", form=form)
	abort(404)

@app.route("/blog/post/<id>", methods=["GET", "POST"])
@login_required
def blog_post_edit(id):
	post = BlogPost.query.get_or_404(id)
	if post.author == current_user.email:
		form = BlogPostForm(request.form, post)
		if form.validate_on_submit():
			form.populate_obj(post)
			post.author = current_user.email
			post.make_slug()
			del post.tags[:]
			for tag_name in request.form.getlist("tags"):
				post.tags.append(get_or_create(Tag, name=tag_name))
			db.session.commit()
			return redirect(request.args.get("next") or url_for("blog"))
		return render_template("blog_post.html", form=form, edit=True)
	abort(404)

