from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import LoginForm, UserRegistrationForm, UserEditForm, ProfileEditForm
from .models import Profile
from .models import Contact
from actions.utils import create_action
from actions.models import Action
from django.core.paginator import Paginator
from images.models import Image
from django.template.loader import render_to_string
from django.db.models import Case, When, BooleanField
from images.models import Story, StoryImage
import random


def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(
                request, username=cd["username"], password=cd["password"]
            )
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponse("Authenticated successfully")
                else:
                    return HttpResponse("Disabled account")
            else:
                return HttpResponse("Invalid login")
    else:
        form = LoginForm()
    return render(request, "account/login.html", {"form": form})


@login_required
def dashboard(request):
    # Display all actions by default
    actions = Action.objects.exclude(user=request.user)
    following_ids = request.user.following.values_list("id", flat=True)
    if following_ids:
        # If user is following others, retrieve only their actions
        actions = actions.filter(user_id__in=following_ids)
    actions = actions.select_related("user", "user__profile").prefetch_related(
        "target"
    )[:10]
    return render(
        request, "account/dashboard.html", {"section": "dashboard", "actions": actions}
    )


@login_required
def home(request):
    user = request.user
    page = int(request.GET.get("page", 1))
    is_initial_load = page == 1 and request.headers.get("x-requested-with") != "XMLHttpRequest"

    # Get followed users (excluding self)
    followed_users = list(
        user.following.exclude(id=user.id).values_list("id", flat=True)
    )

    # Session keys for shuffled image IDs
    session_key = "random_image_ids_combined"

    if is_initial_load or session_key not in request.session:
        # Followed posts
        followed_images = list(
            Image.objects.filter(user__in=followed_users).values_list("id", flat=True)
        )
        random.shuffle(followed_images)

        # Suggested posts (not followed and not self)
        suggested_images = list(
            Image.objects.exclude(user=user)
            .exclude(user__in=followed_users)
            .values_list("id", flat=True)
        )
        random.shuffle(suggested_images)

        # Combine followed first, then suggested
        all_image_ids = followed_images + suggested_images
        request.session[session_key] = all_image_ids
    else:
        all_image_ids = request.session.get(session_key, [])

    # Paginate 5 per scroll
    paginator = Paginator(all_image_ids, 5)
    page_obj = paginator.get_page(page)
    page_id_list = list(page_obj.object_list)

    # Fetch and annotate image objects
    images = (
        Image.objects.filter(id__in=page_id_list, user__isnull=False)
        .select_related("user", "user__profile")
        .annotate(
            is_following=Case(
                When(user__in=followed_users, then=True),
                default=False,
                output_field=BooleanField(),
            )
        )
    )

    # Maintain shuffled order
    images_dict = {img.id: img for img in images}
    images = [images_dict[img_id] for img_id in page_id_list if img_id in images_dict]

    # AJAX response for infinite scroll
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "images/image/list_images.html",
            {"page_obj": page_obj, "images": images, "suggested": False},
            request=request,
        )
        return JsonResponse({
            "html": html,
            "has_more": page_obj.has_next(),
        })

    # Suggested users for top bar
    suggested_users = (
        User.objects.exclude(id=user.id)
        .exclude(id__in=followed_users)
        .select_related("profile")[:100]
    )

    return render(
        request,
        "account/dashboard.html",
        {
            "page_obj": page_obj,
            "images": images,
            "suggested_users": suggested_users,
            "suggested": False,
        },
    )



def register(request):
    if request.method == "POST":
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            # Create a new user object but avoid saving it yet
            new_user = user_form.save(commit=False)
            # Set the chosen password
            new_user.set_password(user_form.cleaned_data["password"])
            # Save the User object
            new_user.save()
            # Create the user profile
            Profile.objects.create(user=new_user)
            create_action(new_user, "has created an account")
            Contact.objects.get_or_create(user_from=new_user, user_to=new_user)
            return redirect("my_profile")
    else:
        user_form = UserRegistrationForm()
    return render(request, "account/register.html", {"user_form": user_form})


@login_required
def edit(request):
    if request.method == "POST":
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(
            instance=request.user.profile, data=request.POST, files=request.FILES
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated " "successfully")
            return redirect("my_profile")

        else:
            messages.error(request, "Error updating your profile")
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
    return render(
        request,
        "account/edit.html",
        {"user_form": user_form, "profile_form": profile_form},
    )


@login_required
def user_list(request):
    query = request.GET.get("q")
    ajax = request.GET.get("ajax")
    users = []
    searched = False
    error = None
    suggestions = []

    if query is not None:
        query = query.strip()

        # Prevent blank searches from proceeding
        if query == "":
            query = None  # Normalize to None so nothing is marked as searched

    if query:
        searched = True
        try:
            # Try exact match first
            user = User.objects.get(username__iexact=query)
            users = [user]
        except User.DoesNotExist:
            error = "User not found"
            # Fuzzy match for similar usernames
            suggestions = list(
                User.objects.filter(username__icontains=query)
                .exclude(username__iexact=query)
                .order_by("username")[:10]
            )

    # AJAX response: return exact or suggested users
    if ajax:
        results = users if users else suggestions
        return JsonResponse(
            [{"username": u.username} for u in results],
            safe=False
        )

    return render(
        request,
        "account/user/list.html",
        {
            "users": users,
            "query": query,
            "searched": searched,
            "error": error,
            "suggestions": suggestions,
        },
    )


@login_required
def user_detail(request, username):
    user = get_object_or_404(User, username=username, is_active=True)
    return render(
        request, "account/user/detail.html", {"section": "people", "user": user}
    )


@login_required
def my_profile(request):
    return render(
        request, "account/user/detail.html", {"section": "people", "user": request.user}
    )


@require_POST
@login_required
def user_follow(request):
    user_id = request.POST.get("id")
    action = request.POST.get("action")
    if user_id and action:
        try:
            user = User.objects.get(id=user_id)
            if action == "follow":
                Contact.objects.get_or_create(user_from=request.user, user_to=user)
                create_action(request.user, "is following", user)
            else:
                # Prevent users from unfollowing themselves
                if user != request.user:
                    Contact.objects.filter(
                        user_from=request.user, user_to=user
                    ).delete()

            # Always ensure self-follow
            Contact.objects.get_or_create(user_from=request.user, user_to=request.user)

            return JsonResponse({"status": "ok"})
        except User.DoesNotExist:
            return JsonResponse({"status": "error"})
    return JsonResponse({"status": "error"})


@login_required
def user_followers(request, username):
    user = get_object_or_404(User, username=username, is_active=True)
    followers = user.followers.all()  # This is a QuerySet of User instances

    paginator = Paginator(followers, 10)  # Show 10 users per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "account/user/follow_list.html",
        {
            "section": "followers",
            "title": f"{user.username}'s followers",
            "people": page_obj,
        },
    )


@login_required
def user_following(request, username):
    user = get_object_or_404(User, username=username, is_active=True)
    following = user.following.all()  # This is a QuerySet of User instances

    paginator = Paginator(following, 10)  # Show 10 users per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "account/user/follow_list.html",
        {
            "section": "following",
            "title": f"{user.username} is following",
            "people": page_obj,
        },
    )


@login_required
def not_following_back(request):
    user = request.user
    following = user.following.all()  # People I follow
    followers = user.followers.all()  # People who follow me

    # Users I follow who do not follow me back
    non_mutual = following.exclude(id__in=followers.values_list("id", flat=True))

    paginator = Paginator(non_mutual, 10)  # Add pagination
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "account/user/follow_list.html",
        {
            "section": "not_following_back",
            "title": "You're following but not followed back",
            "people": page_obj,
        },
    )


@login_required
def upload_story(request):
    if request.method == "POST":
        uploaded_files = request.FILES.getlist("images")

        if not uploaded_files:
            return HttpResponse("No media uploaded", status=400)

        story = Story.objects.create(user=request.user)

        for uploaded_file in uploaded_files:
            content_type = uploaded_file.content_type

            if content_type.startswith("image/"):
                StoryImage.objects.create(story=story, image=uploaded_file)
            elif content_type.startswith("video/"):
                StoryImage.objects.create(story=story, video=uploaded_file)
            else:
                continue  # Ignore unsupported files

        return redirect("user_detail", username=request.user.username)

    return HttpResponse("Invalid method", status=405)
