from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Follow
from django.core.paginator import Paginator
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

@cache_page(20)
def index(request):
    templates = 'posts/index.html'
    posts = Post.objects.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, }
    return render(request, templates, context)


def group_posts(request, slug):
    templates = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, templates, context)


def profile(request, username):
    template = 'posts/profile.html'
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    post_count = post_list.count()
    following = False
    if request.user.is_authenticated:
        if Follow.objects.filter(author=user, user=request.user).exists():
            following = True
    context = {
        'author': user,
        'page_obj': page_obj,
        'post_count': post_count,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post_single = get_object_or_404(Post, id=post_id)
    user = post_single.author
    post_count = Post.objects.filter(author=user).count()
    form = CommentForm(request.POST or None)
    comments = post_single.comments.all()
    context = {
        'post': post_single,
        'post_count': post_count,
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=request.user.username)
        else:
            context = {'form': form}
        return render(request, template, context)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)
    is_edit = True
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post.id)
    if request.method == "POST":
        if form.is_valid():
            post.author = request.user
            post.group = post.group
            post.save()
            return redirect('posts:post_detail', post_id=post.id)
    return render(request, template, {
        'form': form,
        'is_edit': is_edit,
        'post': post
    })

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)

@login_required
def follow_index(request):
    template = 'posts/follow.html'
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, }
    return render(request, template, context)

@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)

@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.get(author=author, user=request.user).delete()
    return redirect('posts:profile', username=username)
