from django.shortcuts import render
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.db import connection

def home(request):
    return render(request, 'core/home.html')

def dash(request):
    return render(request, 'dashboard/dashboard.html')

def logout_view(request):
    request.session.flush()
    return redirect('home')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT StaffId, username, password
                    FROM Staff
                    WHERE username = %s AND password = %s
                """, [username, password])
                user = cursor.fetchone()
                
                if user:
                    # Store user info in session
                    request.session['user_id'] = user[0]
                    request.session['username'] = user[1]  # Store username in session
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Error: You have entered incorrect username or password.')
        else:
            messages.error(request, 'Error: Please enter both username and password.')
    return render(request, 'core/login.html')

def dashboard(request):
    # Check if user is logged in
    if 'user_id' not in request.session:
        return redirect('login')
    
    username = request.session.get('username')
    return render(request, 'dashboard/dashboard.html', {'username': username})  # Updated template path