import json
import logging
import re
from datetime import datetime, time
from io import BytesIO
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from .models import ParentUser
import requests
from PIL import Image
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.timezone import localtime, make_aware, is_naive
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .forms import LoginForm, RegisterForm
from .models import ParentUser, BrowsingLog, RiskAlert
from .utils.alert_engine import send_parent_alert
from .utils.nsfw_detector import get_nsfw_score
from .utils.predict_behaviour import predict_behavior

logger = logging.getLogger(__name__)

# ------------------------ Root Redirect ------------------------

def home_redirect(request):
    if not request.session.get('user_email'):
        return redirect('register')
    parent_email = request.session.get('user_email')
    try:
        parent = ParentUser.objects.get(email=parent_email)
        children = parent.children
        if not children:
            return redirect('dashboard')
        elif len(children) == 1:
            request.session['child_email'] = children[0]
            return redirect('dashboard')
        else:
            return redirect('select_child')
    except ParentUser.DoesNotExist:
        return redirect('register')

# ------------------------ Auth Views ------------------------

def register_user(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            child_emails = form.cleaned_data['child_emails']  # Already a list

            if ParentUser.objects.filter(email=email).exists():
                messages.error(request, "Email already registered.")
            else:
                ParentUser.objects.create_user(
                    full_name=form.cleaned_data['full_name'],
                    email=email,
                    password=form.cleaned_data['password'],
                    children=child_emails
                )
                messages.success(request, "Registration successful. Please log in.")
                return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user = ParentUser.objects.get(email=email)
                if check_password(password, user.password):
                    request.session['user_email'] = user.email
                    request.session['user_name'] = user.full_name
                    request.session['children'] = user.children
                    if len(user.children) == 1:
                        request.session['child_email'] = user.children[0]
                        return redirect('dashboard')
                    return redirect('select_child')
                else:
                    messages.error(request, "Incorrect password.")
            except ParentUser.DoesNotExist:
                messages.error(request, "User not found.")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_user(request):
    logout(request)
    request.session.flush()
    return redirect('login')

# ------------------------ Child Selection ------------------------

def select_child(request):
    if 'user_email' not in request.session:
        return redirect('login')
    try:
        parent = ParentUser.objects.get(email=request.session['user_email'])
        return render(request, 'select_child.html', {'children': parent.children})
    except ParentUser.DoesNotExist:
        return redirect('login')

def set_child(request):
    if request.method == 'POST':
        selected = request.POST.get("child_email")  # ✅ Corrected key name
        request.session["child_email"] = selected
        return redirect("dashboard")
    return redirect('select_child')


@require_POST
def switch_child(request):
    selected_child = request.POST.get('child_email')
    if selected_child:
        request.session['child_email'] = selected_child
    return redirect('dashboard')

# ------------------------ Dashboard ------------------------

def dashboard(request):
    user_email = request.session.get('user_email')
    selected_child = request.session.get('child_email')

    if not user_email:
        messages.error(request, "Please log in first.")
        return redirect('login')

    if not selected_child:
        # ❗ Avoid flash by redirecting immediately before any render happens
        return redirect('select_child')

    try:
        user = ParentUser.objects.get(email=user_email)
    except ParentUser.DoesNotExist:
        messages.error(request, "User not found. Please register.")
        return redirect('register')

    logs = BrowsingLog.objects.filter(child_email=selected_child).order_by('-timestamp')

    for log in logs:
        if log.timestamp and is_naive(log.timestamp):
            log.timestamp = make_aware(log.timestamp)
        log.timestamp = localtime(log.timestamp)

    safe_logs = [log for log in logs if log.label.lower() == "safe"]
    risky_logs = [log for log in logs if log.label.lower() == "risky"]

    return render(request, 'dashboard.html', {
        'logs': logs[:50],
        'safe_count': len(safe_logs),
        'risky_count': len(risky_logs),
        'user_email': user_email,
        'children': user.children,
        'selected_child': selected_child
    })

# ------------------------ Alerts ------------------------

def view_alerts(request):
    if 'user_email' not in request.session:
        return redirect('login')

    alerts = RiskAlert.objects.filter(
        parent_email=request.session['user_email']
    ).order_by('-triggered_at')[:50]

    return render(request, 'view_alerts.html', {'alerts': alerts})

# ------------------------ Browsing Log API ------------------------
import traceback
@csrf_exempt
def log_browsing_data(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        logger.info(f"Received data: {data}")

        required_fields = ["child_email", "url", "title", "query", "image_score", "duration_sec", "hour_of_day"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            return JsonResponse({"error": f"Missing fields: {', '.join(missing)}"}, status=400)

        query = data["query"].strip() or data["title"]
        url = data["url"]
        child_email = data["child_email"]
        hour = data["hour_of_day"]

        if is_duplicate_log(child_email, url):
            logger.info(f"Duplicate log detected for {url}")
            return JsonResponse({"status": "duplicate log detected"}, status=200)

        if "youtube.com" in url or "youtu.be" in url:
            data["image_score"] = fetch_and_analyze_thumbnail(url) or data["image_score"]

        nsfw_score = get_nsfw_score(url)

        input_data = {"query": query, "url": url, "hour": hour}
        # ✅ Correct: use returned dictionary
        result = predict_behavior(input_data)
        logger.info(f"🧪 Predict result: {result} ({type(result)})")

        label = result.get("verdict", "safe")
        reason = result.get("reason", "")
        summary = result.get("summary", "")

        parent = None
        for p in ParentUser.objects.all():
            if child_email in p.children:
                parent = p
                break

        if not parent:
            return JsonResponse({"error": "No parent found for this child"}, status=404)

        log = BrowsingLog.objects.create(
            child_email=child_email,
            parent_email=parent.email,
            title=data["title"],
            url=url,
            query=query,
            duration_sec=data["duration_sec"],
            is_night_time=hour >= 22 or hour <= 6,
            label=label,
            reason=reason,
            summary=summary,
            email_sent=False
        )

        if label == "risky" and not log.email_sent:
            send_parent_alert(log)
            log.email_sent = True
            log.save()

        return JsonResponse({"status": "success"})

    except Exception as e:
        logger.error("Unexpected error in log_browsing_data:")
        logger.error(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)

# ------------------------ Child Email API ------------------------

@csrf_exempt
def validate_child_email(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Only POST allowed"}, status=405)

        data = json.loads(request.body)
        email = data.get("email")

        if not email:
            logger.warning("Child email missing from request")
            return JsonResponse({"error": "Email field is required"}, status=400)

        logger.info(f"🔍 Validating child email: {email}")

        # ✅ Manual lookup to bypass unsupported __contains
        all_parents = ParentUser.objects.all()
        for parent in all_parents:
            if email in parent.children:
                logger.info(f"✅ Child email {email} found under parent {parent.email}")
                return JsonResponse({"valid": True, "parent_email": parent.email})

        logger.warning(f"❌ Child email {email} not found")
        return JsonResponse({"valid": False}, status=404)

    except Exception as e:
        logger.exception("❌ Internal Server Error during child email validation")
        return JsonResponse({"error": str(e)}, status=500)


# ------------------------ Helpers ------------------------
from django.utils.timezone import now

def is_duplicate_log(email, url):
    now_time = now()  # ✅ Properly call the function
    start_of_day = datetime.combine(now_time.date(), time.min)
    end_of_day = datetime.combine(now_time.date(), time.max)
    return BrowsingLog.objects.filter(
        child_email=email,
        url=url,
        timestamp__gte=start_of_day,
        timestamp__lt=end_of_day
    ).first()

def get_youtube_video_id(url):
    match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else None

def fetch_and_analyze_thumbnail(video_url):
    video_id = get_youtube_video_id(video_url)
    if not video_id:
        return None

    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    response = requests.get(thumbnail_url)
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content))
        return analyze_image(img)
    return None

def analyze_image(img):
    # 🔧 Placeholder — replace with real model or heuristic
    return 0.5
