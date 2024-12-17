from django.shortcuts import render
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages




def home(request):
    return render(request, 'core/home.html')

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

def base_admin(request):
    return render(request, 'dashboard/admin/base_admin.html')


def staff_list(request):
    if 'user_id' not in request.session:
        return redirect('login')
    
    username = request.session.get('username')
    updated_id = request.session.get('updated_id')  # Get from session
    
    if updated_id:
        del request.session['updated_id']  # Remove after using once

    # Fetch staff members with role names
    with connection.cursor() as cursor:
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
        
        # Fetch roles for dropdown
        cursor.execute("SELECT roleid, rolename FROM role ORDER BY rolename")
        roles = [{'roleid': row[0], 'rolename': row[1]} for row in cursor.fetchall()]

    context = {
        'username': username,
        'users': users_list,
        'roles': roles,
        'updated_id': updated_id and int(updated_id)  # Convert to int for comparison
    }
    
    return render(request, 'dashboard/admin/staffmanagement.html', context)





def register_staff(request):
    if 'user_id' not in request.session:
        return redirect('login')
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            username = request.POST.get('username')
            password = request.POST.get('password')  # No hashing
            role_name = request.POST.get('role')

            with connection.cursor() as cursor:
                # Get role ID
                cursor.execute("SELECT roleid FROM role WHERE rolename = %s", [role_name])
                role_result = cursor.fetchone()
                
                if not role_result:
                    messages.error(request, 'Invalid role selected.')
                    return redirect('register_staff')
                
                role_id = role_result[0]

                # Insert new staff member
                cursor.execute("""
                    INSERT INTO staff 
                    (name, phonenumber, email, username, password, address, roleid) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [name, phone, email, username, password, address, role_id])
                
                connection.commit()
                messages.success(request, 'Staff member registered successfully!')
                return redirect('staffmanagement')

        except Exception as e:
            connection.rollback()
            messages.error(request, f'Error registering staff member: {str(e)}')
            return redirect('register_staff')

    with connection.cursor() as cursor:
        cursor.execute("SELECT rolename FROM role ORDER BY rolename")
        roles = [{'rolename': row[0]} for row in cursor.fetchall()]
    
    return render(request, 'dashboard/admin/register_staff.html', {'roles': roles})



def edit_staff(request, staff_id):
    if 'user_id' not in request.session:
        return redirect('login')     # Make sure this and all following lines are indented

    with connection.cursor() as cursor:
        if request.method == 'POST':
            try:
                name = request.POST.get('name')
                email = request.POST.get('email')
                phone = request.POST.get('phone')
                address = request.POST.get('address')
                username = request.POST.get('username')
                password = request.POST.get('password')
                role_name = request.POST.get('role')

                # Get role ID
                cursor.execute("SELECT roleid FROM role WHERE rolename = %s", [role_name])
                role_result = cursor.fetchone()
                
                if not role_result:
                    messages.error(request, 'Invalid role selected.')
                    return redirect('edit_staff', staff_id=staff_id)
                
                role_id = role_result[0]

                # Update query with or without password
                if password:
                    cursor.execute("""
                        UPDATE staff 
                        SET name = %s, phonenumber = %s, email = %s, username = %s, 
                            password = %s, address = %s, roleid = %s
                        WHERE staffid = %s
                    """, [name, phone, email, username, password, address, role_id, staff_id])
                else:
                    cursor.execute("""
                        UPDATE staff 
                        SET name = %s, phonenumber = %s, email = %s, username = %s, 
                            address = %s, roleid = %s
                        WHERE staffid = %s
                    """, [name, phone, email, username, address, role_id, staff_id])

                connection.commit()
                messages.success(request, 'Staff member updated successfully!')
                return redirect('staffmanagement')

            except Exception as e:
                connection.rollback()
                messages.error(request, f'Error updating staff member: {str(e)}')
                return redirect('edit_staff', staff_id=staff_id)

        # Get staff data for the form
        cursor.execute("""
            SELECT s.staffid, s.name, s.phonenumber, s.email, s.username, 
                   s.address, r.rolename
            FROM staff s
            JOIN role r ON s.roleid = r.roleid
            WHERE s.staffid = %s
        """, [staff_id])
        staff_data = cursor.fetchone()

        if not staff_data:
            messages.error(request, 'Staff member not found.')
            return redirect('staffmanagement')

        staff = {
            'staffid': staff_data[0],
            'name': staff_data[1],
            'phonenumber': staff_data[2],
            'email': staff_data[3],
            'username': staff_data[4],
            'address': staff_data[5],
            'rolename': staff_data[6]
        }

        # Get roles for dropdown
        cursor.execute("SELECT rolename FROM role ORDER BY rolename")
        roles = [{'rolename': row[0]} for row in cursor.fetchall()]

        context = {
            'staff': staff,
            'roles': roles
        }

        return render(request, 'dashboard/admin/edit_staff.html', context)