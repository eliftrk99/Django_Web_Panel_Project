from django.shortcuts import redirect,render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from account.models import UserProfile

def register_request(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        image = request.POST["image"]
        username = request.POST["username"]
        email = request.POST["email"]
        firstname = request.POST["firstname"]
        lastname = request.POST["lastname"]
        city = request.POST["city"]
        province = request.POST["province"]
        birthDate = request.POST["birthDate"]
        cinsiyet = request.POST["cinsiyet"]
        phone = request.POST["phone"]
        password = request.POST["password"]
        repassword = request.POST["repassword"]

        user = authenticate(request, username=username, password=password)

        if password == repassword:
            if User.objects.filter(username=username).exists():
                return render(request, "account/register.html",
                {
                    "error": "Username already exists",
                    "image": image,
                    "username": username,
                    "email": email,
                    "firstname": firstname,
                    "lastname": lastname,
                    "city": city,
                    "province": province,
                    "birthDate": birthDate,
                    "cinsiyet": cinsiyet,
                    "phone": phone
                })
            else:
                if User.objects.filter(email=email).exists():
                    return render(request, "account/register.html", 
                    {
                        "error": "Email already exists",
                        "image": image,
                        "username": username,
                        "email": email,
                        "firstname": firstname,
                        "lastname": lastname,
                        "city": city,
                        "province": province,
                        "birthDate": birthDate,
                        "cinsiyet": cinsiyet,
                        "phone": phone
                    })
                else:
                    user = User.objects.create_user(image=image, username=username, email=email, first_name=firstname, last_name=lastname, city=city, province=province, birthDate=birthDate, cinsiyet=cinsiyet, phone=phone, password=password)
                    user.save()
                    return redirect("login")
        else:
            return render(request, "account/register.html",
            {
                "error": "Password and Re-Password do not match",
                "image": image,
                "username": username,
                "email": email,
                "firstname": firstname,
                "lastname": lastname,
                "city": city,
                "province": province,
                "birthDate": birthDate,
                "cinsiyet": cinsiyet,
                "phone": phone
            })

    return render(request, "account/register.html")

def login_request(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            return render(request, "account/login.html", {"error": "Invalid username or password"})

    return render(request, "account/login.html")


def profile_request(request):
    if not request.user.is_authenticated:
        return redirect("login")

    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        is_profile_update = ('update' in request.POST) or 'image' in request.FILES or any(
            key in request.POST for key in ['username', 'email', 'firstname', 'lastname', 'city', 'province', 'phone', 'birthDate', 'cinsiyet']
        )

        if is_profile_update:
            user.username = request.POST.get('username', user.username)
            user.email = request.POST.get('email', user.email)
            user.first_name = request.POST.get('firstname', user.first_name)
            user.last_name = request.POST.get('lastname', user.last_name)
            profile.phone = request.POST.get('phone', profile.phone)
            profile.city = request.POST.get('city', profile.city)
            profile.province = request.POST.get('province', profile.province)
            if 'image' in request.FILES:
                profile.image = request.FILES['image']
            profile.save()
            user.save()
            return redirect('profile')

        if 'change_password' in request.POST:
            password = request.POST.get('password', '')
            new_password = request.POST.get('newpassword', '')
            renew_password = request.POST.get('renewpassword', '')
            if not user.check_password(password):
                return render(request, 'account/profile.html', {'error': 'Mevcut parola hatalı.', 'profile': profile})
            if new_password != renew_password:
                return render(request, 'account/profile.html', {'error': 'Yeni parolalar eşleşmiyor.', 'profile': profile})
            user.set_password(new_password)
            user.save()
            return redirect('login')

    return render(request, 'account/profile.html', {
        'city': profile.city,
        'province': profile.province,
        'phone': profile.phone,
        'birthDate': '',
        'cinsiyet': '',
        'profile': profile,
    })

def logout_request(request):
    logout(request)
    return redirect("home")
