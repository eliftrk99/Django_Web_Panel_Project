from django.shortcuts import redirect,render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

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
    
    return render(request, "account/profile.html")

def logout_request(request):
    logout(request)
    return redirect("home")
