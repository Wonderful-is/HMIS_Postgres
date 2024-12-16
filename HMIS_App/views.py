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





    ###############     Admin Panel #################################################


def admin_dashboard(request):
    if 'user_id' not in request.session:
        return redirect('login')
    
    username = request.session.get('username')
    
    # Fetch users
    with connection.cursor() as cursor:
        # Fetch staff members with role names
        cursor.execute("""
            SELECT s.staffid, s.name, s.phonenumber, s.email, 
                   s.username, s.address, r.rolename
            FROM staff s
            JOIN role r ON s.roleid = r.roleid
            ORDER BY s.staffid
        """)
        users = cursor.fetchall()
        users_list = []
        for user in users:
            users_list.append({
                'staffid': user[0],
                'name': user[1],
                'phone': user[2],
                'email': user[3],
                'username': user[4],
                'address': user[5],
                'role': user[6]
            })
        
        # Fetch roles for the dropdown
        cursor.execute("SELECT roleid, rolename FROM role ORDER BY rolename")
        roles = [{'roleid': row[0], 'rolename': row[1]} for row in cursor.fetchall()]

    context = {
        'username': username,
        'users': users_list,
        'roles': roles
    }
    
    return render(request, 'dashboard/admin/admin_dashboard.html', context)

def register_staff(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        password = request.POST.get('password')
        role_id = request.POST.get('role')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO staff 
                    (name, username, email, phonenumber, address, password, roleid)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING staffid
                """, [name, username, email, phone, address, password, role_id])
                
                staff_id = cursor.fetchone()[0]
                messages.success(request, 'Staff member registered successfully!')
                
        except Exception as e:
            messages.error(request, f'Error registering staff member: {str(e)}')
            
    return redirect('admin_dashboard')