from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import ImageCreateForm
from .models import Image, Comment
from actions.utils import create_action
from django.conf import settings
import redis
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Story, StoryImage
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
from django.views.decorators.csrf import csrf_exempt
import json


r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
)


@login_required
def image_create(request):
    if request.method == "POST":
        images = request.FILES.getlist("image")
        form = ImageCreateForm(request.POST)

        if form.is_valid():
            for img in images:
                instance = Image(
                    user=request.user,
                    title=form.cleaned_data.get("title"),
                    url=form.cleaned_data.get("url"),
                    description=form.cleaned_data.get("description"),
                )
                instance.image = img
                instance.save()

            messages.success(request, "Images uploaded successfully")
            return redirect("user_detail", username=request.user.username)
    else:
        form = ImageCreateForm()

    return render(request, "images/image/create.html", {"form": form})


def image_detail(request, id, slug):
    image = get_object_or_404(Image, id=id, slug=slug)
    # increment total image views by 1
    total_views = r.incr(f"image:{image.id}:views")
    # increment image ranking by 1
    r.zincrby("image_ranking", 1, image.id)
    return render(
        request,
        "images/image/detail.html",
        {"section": "images", "image": image, "total_views": total_views},
    )


@login_required
@require_POST
def image_like(request):
    image_id = request.POST.get("id")
    action = request.POST.get("action")
    if image_id and action:
        try:
            image = Image.objects.get(id=image_id)
            if action == "like":
                image.users_like.add(request.user)
                create_action(request.user, "likes", image)
            else:
                image.users_like.remove(request.user)
            return JsonResponse({"status": "ok"})
        except Image.DoesNotExist:
            pass
    return JsonResponse({"status": "error"})


@login_required
def image_list(request):
    followed_ids = request.user.following.values_list("id", flat=True)
    followed_images = Image.objects.filter(user__in=followed_ids).order_by("-created")
    other_images = Image.objects.exclude(user__in=followed_ids).order_by("-created")

    all_images = list(followed_images) + list(other_images)

    paginator = Paginator(all_images, 50)
    page = request.GET.get("page")
    images_only = request.GET.get("images_only")

    try:
        images = paginator.page(page)
    except PageNotAnInteger:
        images = paginator.page(1)
    except EmptyPage:
        if images_only:
            return HttpResponse("")
        images = paginator.page(paginator.num_pages)

    new_user = (
        not followed_images.exists()
        and not Image.objects.filter(user=request.user).exists()
    )

    grouped_stories = dict(get_active_stories_grouped_by_user())

    context = {
        "section": "images",
        "images": images,
        "new_user": new_user,
        "grouped_stories": grouped_stories,
    }

    if images_only:
        return render(request, "images/image/list_images.html", context)
    print("Grouped stories:", grouped_stories)

    return render(request, "images/image/list.html", context)



@login_required
def image_ranking(request):
    # get image ranking dictionary
    image_ranking = r.zrange("image_ranking", 0, -1, desc=True)[:10]
    image_ranking_ids = [int(id) for id in image_ranking]
    # get most viewed images
    most_viewed = list(Image.objects.filter(id__in=image_ranking_ids))
    most_viewed.sort(key=lambda x: image_ranking_ids.index(x.id))
    return render(
        request,
        "images/image/ranking.html",
        {"section": "images", "most_viewed": most_viewed},
    )


@require_POST
@login_required
def image_comment(request):
    image_id = request.POST.get("image_id")
    text = request.POST.get("comment")

    try:
        image = Image.objects.get(id=image_id)
        comment = Comment.objects.create(image=image, user=request.user,
                                         text=text)
        return JsonResponse(
            {"status": "ok", "text": comment.text,
             "user": request.user.first_name}
        )
    except Image.DoesNotExist:
        return JsonResponse({"status": "error"})


def image_list_view(request):
    query = request.GET.get("q")
    if query:
        users = User.objects.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )
        images = Image.objects.filter(user__in=users).select_related("user")
    else:
        images = Image.objects.all()

    context = {
        "images": images,
    }
    if request.GET.get("images_only"):
        return render(request, "images/image/list_images.html", context)
    return render(request, "images/image/bookmarked.html", context)


@require_POST
@login_required
def ajax_delete_image(request):
    image_id = request.POST.get("id")
    try:
        image = Image.objects.get(id=image_id, user=request.user)
        image.delete()
        return JsonResponse({"status": "ok"})
    except Image.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Not authorized or post not found."}
        )


@login_required
def story_list(request):
    stories = (
        Story.objects.filter(created__gte=timezone.now() - timedelta(hours=24))
        .select_related("user")
        .distinct("user")
    )
    return render(request, "images/image/story_list.html",
                  {"stories": stories})


@login_required
def story_detail(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    return render(request, 'images/image/story_detail.html', {'story': story})


def get_active_stories_grouped_by_user():
    grouped = defaultdict(list)
    stories = Story.objects.filter(
        created__gte=timezone.now() - timedelta(hours=24)
    ).select_related('user').order_by('created')

    for story in stories:
        grouped[story.user].append(story)

    return grouped


@login_required
def explore_view(request):
    grouped_stories = get_active_stories_grouped_by_user()
    return render(request, 'images/image/list.html', {
        'grouped_stories': grouped_stories,
        'section': 'images'
    })


@csrf_exempt
@login_required
def delete_story_image(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        image_url = data.get('image_url')
        if image_url:
            try:
                img = StoryImage.objects.get(image=image_url.replace('/media/', ''))
                if img.story.user == request.user:
                    img.delete()
                    return JsonResponse({'status': 'ok'})
            except StoryImage.DoesNotExist:
                pass
    return JsonResponse({'status': 'error'})

