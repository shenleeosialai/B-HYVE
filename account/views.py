from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import LoginForm, UserRegistrationForm, \
    UserEditForm, ProfileEditForm
from .models import Profile
from .models import Contact
from actions.utils import create_action
from actions.models import Action
from django.core.paginator import Paginator


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
        request, "account/dashboard.html",
        {"section": "dashboard", "actions": actions}
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
            return redirect("my_profile", {"new_user": new_user})
    else:
        user_form = UserRegistrationForm()
    return render(request, "account/register.html", {"user_form": user_form})


@login_required
def edit(request):
    if request.method == "POST":
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(
            instance=request.user.profile, data=request.POST,
            files=request.FILES
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
    query = request.GET.get('q')
    ajax = request.GET.get('ajax')
    users = []
    searched = False

    if query is not None:
        query = query.strip()
        searched = True
        if query:
            try:
                user = User.objects.get(username__iexact=query)
                users = [user]
            except User.DoesNotExist:
                users = []
        else:
            users = []  # Empty input still counts as "searched"

    if ajax:
        return JsonResponse(
            [{'username': u.username} for u in users],
            safe=False
        )

    return render(request, 'account/user/list.html', {
        'users': users,
        'query': query,
        'searched': searched,
    })


@login_required
def user_detail(request, username):
    user = get_object_or_404(User, username=username, is_active=True)
    return render(
        request, "account/user/detail.html",
        {"section": "people", "user": user}
    )


@login_required
def my_profile(request):
    return render(
        request, "account/user/detail.html",
        {"section": "people", "user": request.user}
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
                Contact.objects.get_or_create(user_from=request.user,
                                              user_to=user)
                create_action(request.user, "is following", user)
            else:
                Contact.objects.filter(user_from=request.user,
                                       user_to=user).delete()
            return JsonResponse({"status": "ok"})
        except User.DoesNotExist:
            return JsonResponse({"status": "error"})
    return JsonResponse({"status": "error"})


@login_required
def user_followers(request, username):
    user = get_object_or_404(User, username=username, is_active=True)
    followers = user.followers.all()  # This is a QuerySet of User instances

    paginator = Paginator(followers, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'account/user/follow_list.html', {
        'section': 'followers',
        'title': f"{user.username}'s followers",
        'people': page_obj
    })


@login_required
def user_following(request, username):
    user = get_object_or_404(User, username=username, is_active=True)
    following = user.following.all()  # This is a QuerySet of User instances

    paginator = Paginator(following, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'account/user/follow_list.html', {
        'section': 'following',
        'title': f"{user.username} is following",
        'people': page_obj
    })


@login_required
def not_following_back(request):
    user = request.user
    following = user.following.all()          # People I follow
    followers = user.followers.all()          # People who follow me

    # Users I follow who do not follow me back
    non_mutual = following.exclude(id__in=followers.values_list('id',
                                                                flat=True))

    paginator = Paginator(non_mutual, 10)     # Add pagination
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'account/user/follow_list.html', {
        'section': 'not_following_back',
        'title': "You're following but not followed back",
        'people': page_obj
    })
