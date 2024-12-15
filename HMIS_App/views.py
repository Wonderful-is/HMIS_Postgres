from django.shortcuts import render
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from django.contrib.auth.hashers import check_password


def home(request):
    return render(request, 'core/home.html')

# def login_view(request):
#     return render(request, 'core/login.html')

def dash(request):
    return render(request, 'dashboard/dashboard.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            # Raw SQL query to check user
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT StaffId, username, password 
                    FROM Staff 
                    WHERE username = %s AND password = %s
                """, [username, password])  # Direct password comparison
                user = cursor.fetchone()
                
                if user:
                    # Login successful
                    request.session['user_id'] = user[0]
                    messages.success(request, 'Login successful!')
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please enter both username and password.')
            
    return render(request, 'core/login.html')

def dashboard(request):
    if 'user_id' not in request.session:
        return redirect('login')
        
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT username, email, date_joined 
            FROM auth_user 
            WHERE id = %s
        """, [request.session['user_id']])
        user_data = cursor.fetchone()
        
    context = {
        'username': user_data[0],
        'email': user_data[1],
        'joined_date': user_data[2]
    }
    return render(request, 'dashboard/dashboard.html', context)