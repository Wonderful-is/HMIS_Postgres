from django.shortcuts import render
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages

from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
import json

from datetime import datetime





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
                    SELECT staff_id, username, password
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
    user_id = request.session.get('user_id')
    return render(request, 'dashboard/dashboard.html', {'username': username, 'user_id': user_id})  # Updated template path





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
            SELECT s.staff_id, s.full_name, s.email, s.username,
                   s.password, s.address, r.role_id, s.phone_number
            FROM staff s
            JOIN roles r ON s.role_id = r.role_id
            ORDER BY s.staff_id 
        """)
        users = cursor.fetchall()
        users_list = []
        for user in users:
            users_list.append({
                'staff_id': user[0],
                'full_name': user[1],
                'email': user[2],
                'username': user[3],
                'password': user[4],
                'address': user[5],
                'role_id': user[6],
                'phone_number': user[7],
                #'phone_number': user[5]
            })

        # Fetch roles for dropdown
        cursor.execute("SELECT role_id, role_name FROM roles ORDER BY role_name")
        roles = [{'role_id': row[0], 'role_name': row[1]} for row in cursor.fetchall()]

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
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number')
            address = request.POST.get('address')
            username = request.POST.get('username')
            password = request.POST.get('password')  # No hashing
            role_name = request.POST.get('role')

            with connection.cursor() as cursor:
                # Get role ID
                cursor.execute("SELECT role_id FROM roles WHERE role_name = %s", [role_name])
                role_result = cursor.fetchone()
                
                if not role_result:
                    messages.error(request, 'Invalid roles selected.')
                    return redirect('register_staff')
                
                role_id = role_result[0]

                # Insert new staff member
                cursor.execute("""
                    INSERT INTO staff 
                    (full_name, phone_number, email, username, password, address, role_id) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [full_name, phone_number, email, username, password, address, role_id])
                
                connection.commit()
                messages.success(request, 'Staff member registered successfully!')
                return redirect('staffmanagement')

        except Exception as e:
            connection.rollback()
            messages.error(request, f'Error registering staff member: {str(e)}')
            return redirect('register_staff')

    with connection.cursor() as cursor:
        cursor.execute("SELECT role_name FROM roles ORDER BY role_name")
        roles = [{'role_name': row[0]} for row in cursor.fetchall()]
    
    return render(request, 'dashboard/admin/register_staff.html', {'roles': roles})



def edit_staff(request, staff_id):
    if 'user_id' not in request.session:
        return redirect('login')     # Make sure this and all following lines are indented
    
    username = request.session.get('username')
    user_id = request.session.get('user_id')

    with connection.cursor() as cursor:
        if request.method == 'POST':
            try:

                full_name = request.POST.get('full_name')
                email = request.POST.get('email')
                phone_number = request.POST.get('phone_number')
                address = request.POST.get('address')
                username = request.POST.get('username')
                password = request.POST.get('password')  
                role_name = request.POST.get('role')


                 # Get role ID
                cursor.execute("SELECT role_id FROM roles WHERE role_name = %s", [role_name])
                role_result = cursor.fetchone()
                
                if not role_result:
                    messages.error(request, 'Invalid roles selected.')
                    return redirect('edit_staff')
                
                role_id = role_result[0]



                

                # Update query with or without password
                if password:
                    cursor.execute("""
                        UPDATE staff 
                        SET full_name = %s, phone_number = %s, email = %s, username = %s, 
                            password = %s, address = %s, role_id = %s
                        WHERE staff_id = %s
                    """, [full_name, phone_number, email, username, password, address, role_id, staff_id])
                else:
                    cursor.execute("""
                        UPDATE staff 
                        SET full_name = %s, phone_number = %s, email = %s, username = %s, 
                            address = %s, role_id = %s
                        WHERE staff_id = %s
                    """, [full_name, phone_number, email, username, address, role_id, staff_id])

                connection.commit()
                messages.success(request, 'Staff member updated successfully!')
                return redirect('staffmanagement')

            except Exception as e:
                connection.rollback()
                messages.error(request, f'Error updating staff member: {str(e)}')
                return redirect('edit_staff', staff_id=staff_id)

        # Get staff data for the form
        cursor.execute("""
            SELECT s.staff_id, s.full_name, s.phone_number, s.email, s.username, 
                   s.address, r.role_name
            FROM staff s
            JOIN roles r ON s.role_id = r.role_id
            WHERE s.staff_id = %s
        """, [staff_id])
        staff_data = cursor.fetchone()

        if not staff_data:
            messages.error(request, 'Staff member not found.')
            return redirect('staffmanagement')

        staff = {
            'staff_id': staff_data[0],
            'full_name': staff_data[1],
            'phone_number': staff_data[2],
            'email': staff_data[3],
            'username': staff_data[4],
            'address': staff_data[5],
            'role_name': staff_data[6]
        }

        # Get roles for dropdown
        cursor.execute("SELECT role_name FROM roles ORDER BY role_name")
        roles = [{'role_name': row[0]} for row in cursor.fetchall()]

        context = {
            'staff': staff,
            'roles': roles,
            'username' : username,
            'user_id' : user_id
        }

        return render(request, 'dashboard/admin/edit_staff.html', context)




#Delete staff

def delete_staff(request, staff_id):
    if request.method == 'DELETE':
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM staff WHERE staff_id = %s", [staff_id])
            return JsonResponse({'message': 'Staff deleted successfully.'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method.'}, status=400)



# Role management

# List Role
def role_list(request):
    if 'user_id' not in request.session:
        return redirect('login')

    username = request.session.get('username')

    try:
        with connection.cursor() as cursor:
            # Ensure the column names match your actual table schema
            cursor.execute("SELECT role_id, role_name, role_description FROM roles ORDER BY role_name")
            roles_data = cursor.fetchall()

            print(f"Roles fetched from the database: {roles_data}")  # Debugging line

            # Handle empty roles without redirecting
            roles_list = [{
                'roleid': row[0],
                'rolename': row[1],
                'roledescription': row[2]
            } for row in roles_data]

        context = {
            'username': username,
            'roles': roles_list,
        }

        if not roles_data:
            context['message'] = "No roles found in the database."

        return render(request, 'dashboard/admin/rolemanagement.html', context)

    except Exception as e:
        print(f"Database error: {str(e)}")
        messages.error(request, f"Database error: {str(e)}")
        return render(request, 'dashboard/admin/rolemanagement.html', {'username': username, 'error': str(e)})


# Register a New Role



def register_role(request):
    if request.method == 'POST':
        role_name = request.POST.get('role_name')
        role_description = request.POST.get('role_description')

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO roles (role_name, role_description) VALUES (%s, %s)",
                    [role_name, role_description]
                )
            messages.success(request, 'Roles added successfully!')
            return redirect('rolemanagement')
        except Exception as e:
            messages.error(request, f'Error: {e}')
            return redirect('register_role')

    return render(request, 'dashboard/admin/register_role.html')





# Edit Role
def edit_role(request, role_id):
    if 'user_id' not in request.session:
        return redirect('login')

    with connection.cursor() as cursor:
        if request.method == 'POST':
            role_name = request.POST.get('role_name')
            role_description = request.POST.get('role_description')

            try:
                cursor.execute("""
                    UPDATE roles
                    SET role_name = %s, role_description = %s
                    WHERE role_id = %s
                """, [role_name, role_description, role_id])

                connection.commit()
                messages.success(request, 'Role updated successfully!')
                return redirect('rolemanagement')

            except Exception as e:
                connection.rollback()
                messages.error(request, f'Error updating role: {str(e)}')
                return redirect('edit_role', role_id=role_id)

        # Get role data for editing
        cursor.execute("""
            SELECT role_name, role_description FROM roles WHERE role_id = %s
        """, [role_id])
        role_data = cursor.fetchone()

        if not role_data:
            messages.error(request, 'Role not found.')
            return redirect('rolemanagement')

        role = {
            'role_name': role_data[0],
            'role_description': role_data[1]
        }

        context = {'role': role}
        return render(request, 'dashboard/admin/edit_role.html', context)

# Delete Role
def delete_role(request, role_id):
    if request.method == 'DELETE':
        try:
            # Use raw SQL to delete the role
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM roles WHERE role_id = %s", [role_id])

            return JsonResponse({'message': 'Role deleted successfully.'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)




#Department Managment

def department_list(request):
    if 'user_id' not in request.session:
        return redirect('login')

    username = request.session.get('username')

    try:
        with connection.cursor() as cursor:
            # Fetch department data from the database
            cursor.execute("SELECT department_id, department_name, department_description FROM departments ORDER BY department_name")
            departments_data = cursor.fetchall()

            print(f"departments fetched from the database: {departments_data}")  # Debugging line

            # If no departments are found
            if not departments_data:
                return render(request, 'dashboard/admin/departmentmanagement.html', {
                    'username': username,
                    'message': "No departments found in the database."
                })

            # Populate the department list with data
            departments_list = [{
                'department_id': row[0],
                'department_name': row[1],
                'department_description': row[2]
            } for row in departments_data]

        # Pass the data to the template
        context = {
            'username': username,
            'departments': departments_list,
        }

        return render(request, 'dashboard/admin/departmentmanagement.html', context)

    except Exception as e:
        print(f"Database error: {str(e)}")
        messages.error(request, f"Database error: {str(e)}")
        return render(request, 'dashboard/admin/departmentmanagement.html', {'username': username, 'error': str(e)})


# Register Department

def register_department(request):
    if request.method == 'POST':
        department_name = request.POST.get('department_name')
        department_description = request.POST.get('department_description')

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO departments (department_name, department_description) VALUES (%s, %s)",
                    [department_name, department_description]
                )
            messages.success(request, 'Departments added successfully!')
            return redirect('departmentmanagement')
        except Exception as e:
            messages.error(request, f'Error: {e}')
            return redirect('register_department')

    return render(request, 'dashboard/admin/register_department.html')






# Edit Department
def edit_department(request, department_id):
    # Ensure the user is logged in
    if 'user_id' not in request.session:
        return redirect('login')

    # Establish a connection to the database
    with connection.cursor() as cursor:
        if request.method == 'POST':
            # Get data from the form
            department_name = request.POST.get('department_name')
            department_description = request.POST.get('department_description')

            try:
                # Update the department in the database
                cursor.execute("""
                    UPDATE departments
                    SET department_name = %s, department_description = %s
                    WHERE department_id = %s
                """, [department_name, department_description, department_id])

                connection.commit()  # Commit the transaction
                messages.success(request, 'Department updated successfully!')
                return redirect('departmentmanagement')  # Redirect to the department list page

            except Exception as e:
                connection.rollback()  # Rollback the transaction if there's an error
                messages.error(request, f'Error updating department: {str(e)}')
                return redirect('edit_department', department_id=department_id)

        # If it's a GET request, fetch the department data
        cursor.execute("""
            SELECT department_name, department_description FROM departments WHERE department_id = %s
        """, [department_id])
        department_data = cursor.fetchone()

        if not department_data:
            messages.error(request, 'Department not found.')
            return redirect('departmentmanagement')  # Redirect if no department is found

        # Prepare the department data for editing
        context = {
            'department': {
                'department_name': department_data[0],
                'department_description': department_data[1]
            }
        }

        # Render the edit department page with the fetched department data
        return render(request, 'dashboard/admin/edit_department.html', context)



# # Delete Department


# Delete Department
def delete_department(request, department_id):
    if request.method == 'DELETE':
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM department WHERE department_id = %s", [department_id])
            return JsonResponse({'message': 'Department deleted successfully.'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method.'}, status=400)


















def delete_role(request, role_id):
    if 'user_id' not in request.session:
        return redirect('login')

    try:
        print(f"Attempting to delete role with ID: {role_id}")  # Debugging line

        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM role WHERE roleid = %s", [role_id])
            connection.commit()

        messages.success(request, 'Role deleted successfully!')
        return redirect('rolemanagement')

    except Exception as e:
        connection.rollback()
        print(f"Database error while deleting role: {str(e)}")  # Debugging line
        messages.error(request, f'Failed to delete role: {str(e)}')
        return redirect('rolemanagement')





# Delete staff
def delete_staff(request, staff_id):
    if 'user_id' not in request.session:
        return redirect('login')

    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM staff WHERE staffid = %s", [staff_id,])
            connection.commit()

        messages.success(request, 'staff deleted successfully!')
        return redirect('staffmanagement')

    except Exception as e:
        connection.rollback()
        messages.error(request, f'Failed to delete staff: {str(e)}')
        return redirect('staffmanagement')

############################################################################################################################################################################

####################################                                ALMONER                                        ####################################################################

######################################################################################################################################################################

def base_almoner(request):
    # Check if user is logged in
    if 'user_id' not in request.session:
        return redirect('login')

    username = request.session.get('username')
    user_id = request.session.get('user_id')

    return render(request, 'dashboard/almoner/base_almoner.html', {'username': username, 'user_id': user_id})





def patient_list(request):
    if 'user_id' not in request.session:
        return redirect('login')
    
    username = request.session.get('username')
    updated_id = request.session.get('updated_id')  # Get from session
    user_id = request.session.get('user_id')

    if updated_id:
        del request.session['updated_id']  # Remove after using once

    # Fetch staff members with role names
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.patient_id, p.full_name, p.date_of_birth, p.age,
                   p.gender, p.address, p.phone_number, p.email, 
                   p.dependent_name, p.dependent_contact, p.relationship_with_dependent,
                  p.insurance, p.registered_by
            FROM patients p
            ORDER BY p.patient_id 
        """)

        patients = cursor.fetchall()
        patients_list = []
        for patient in patients:
            patients_list.append({
                'patient_id': patient[0],
                'full_name': patient[1],
                'date_of_birth': patient[2],
                'age': patient[3],
                'gender': patient[4],
                'address': patient[5],
                'phone_number': patient[6],
                'email': patient[7],
                'dependent_name': patient[8],
                'dependent_contact': patient[9],
                'relationship_with_dependent': patient[10],
                'insurance': patient[11],
                'registered_by': patient[12],
            })

    context = {
        'username': username,
        'user_id': user_id,
        'patients': patients_list,
    }
    
    return render(request, 'dashboard/almoner/patientmanagement.html', context)






# View a Specific Patient
def view_patient(request, patient_id):
    if 'user_id' not in request.session:  # Ensure the user is logged in
        return redirect('login')

    # Query the database for the specific patient's details
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.patient_id, p.full_name, p.date_of_birth, p.age,
                   p.gender, p.address, p.phone_number, p.email, 
                   p.dependent_name, p.dependent_contact, p.relationship_with_dependent,
                   p.insurance, p.registered_by, p.created_at 
            FROM patients p
            WHERE p.patient_id = %s ORDER BY p.created_at DESC
        """, [patient_id])
        patient = cursor.fetchone()

    # Handle case when patient is not found
    if not patient:
        return HttpResponse("Patient not found", status=404)

    # Map the result to a dictionary for the template
    patient_details = {
        'patient_id': patient[0],
        'full_name': patient[1],
        'date_of_birth': patient[2],
        'age': patient[3],
        'gender': patient[4],
        'address': patient[5],
        'phone_number': patient[6],
        'email': patient[7],
        'dependent_name': patient[8],
        'dependent_contact': patient[9],
        'relationship_with_dependent': patient[10],
        'insurance': patient[11],
        'registered_by': patient[12],
    }

    # Pass the patient details to the template
    context = {
        'patient': patient_details,
    }
    return render(request, 'dashboard/almoner/view_patient.html', context)





# Visit Management
#********************#

def visit_list(request):
    visits_list = []

    # Check if the user is logged in
    if 'user_id' not in request.session:
        return redirect('login')

    username = request.session.get('username', 'Guest')

    try:
        with connection.cursor() as cursor:
            # Modify the query to join the 'visits' table with the 'patients' table
            cursor.execute(
                """
                	SELECT v.visit_id, v.visit_date, v.reason_for_visit, p.full_name 
                    FROM visit v
                    JOIN patients p ON v.patient_id = p.patient_id
                    ORDER BY v.visit_date DESC

                """
            )
            visits_data = cursor.fetchall()

            # If the table is empty, set a default message
            if not visits_data:
                visits_list = []
                raise ValueError("No visits found in the database.")  # Custom exception for empty result

            # Transform the data into a list of dictionaries
            visits_list = [
                {
                    'visit_id': row[0],
                    'visit_date': row[1],
                    'reason_for_visit': row[2] or "N/A",  # Default to "N/A" if reason_for_visit is NULL
                    'patient_name': row[3] or "Unknown"  # Default to "Unknown" if patient_name is NULL
                }
                for row in visits_data
            ]

        context = {
            'username': username,
            'visits': visits_list,
        }

        return render(request, 'dashboard/almoner/visitmanagement.html', context)

    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error while fetching visits data: {str(e)}")

        # Handle database errors and return the error message to the template
        messages.error(request, f"Error occurred while fetching visits data: {str(e)}")
        return render(request, 'dashboard/almoner/visitmanagement.html', {
            'username': username,
            'visits': visits_list,
            'message': f"Error: {str(e)}"
        })


# View a Specific Patient
def view_visit(request, visit_id):
    if 'user_id' not in request.session:  # Ensure the user is logged in
        return redirect('login')

    # Query the database for the specific visit details
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT v.visit_id, v.visit_date, v.reason_for_visit, v.patient_id,
                   p.full_name, p.date_of_birth, p.age, p.gender, 
                   p.address, p.phone_number, p.email
            FROM visit v
            JOIN patients p ON v.patient_id = p.patient_id
            WHERE v.visit_id = %s
        """, [visit_id])
        visit = cursor.fetchone()

    # Handle case when visit is not found
    if not visit:
        return HttpResponse("Visit not found", status=404)

    # Map the result to a dictionary for the template
    visit_details = {
        'visit_id': visit[0],
        'visit_date': visit[1],
        'reason_for_visit': visit[2],
        'patient_id': visit[3],
        'patient_full_name': visit[4],
        'patient_date_of_birth': visit[5],
        'patient_age': visit[6],
        'patient_gender': visit[7],
        'patient_address': visit[8],
        'patient_phone_number': visit[9],
        'patient_email': visit[10],
    }

    # Pass the visit details to the template
    context = {
        'visit': visit_details,
    }

    return render(request, 'dashboard/almoner/view_visit.html', context)




#############################    appointment    #########################################################




# Appointment Management
#********************#

def appointment_list(request):
    # Initialize the appointments list
    appointments_list = []

    # Check if the user is logged in
    if 'user_id' not in request.session:
        return redirect('login')

    # Get the username from the session, defaulting to 'Guest'
    username = request.session.get('username', 'Guest')

    try:
        # Fetch appointments data from the database
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    a.appointment_id, 
                    a.appointment_date, 
                    a.reason_for_appointment, 
                    p.full_name,
                    a.status
                FROM 
                    appointment a
                JOIN 
                    patients p 
                ON 
                    a.patient_id = p.patient_id
                ORDER BY 
                    a.appointment_date DESC
                    
                """
            )
            appointments_data = cursor.fetchall()

        # Handle the case where no appointments are found
        if not appointments_data:
            raise ValueError("No appointments found in the database.")

        # Transform the data into a list of dictionaries
        appointments_list = [
            {
                'appointment_id': row[0],
                'appointment_date': row[1],
                'reason_for_appointment': row[2] or "N/A",  # Default to "N/A" if NULL
                'patient_name': row[3] or "Unknown" ,        # Default to "Unknown" if NULL
                'status': row[4]
            }
            for row in appointments_data
        ]

    except ValueError as ve:
        # Handle the specific case of no appointments found
        messages.warning(request, str(ve))
    except Exception as e:
        # Log unexpected errors and display an error message to the user
        print(f"Error while fetching appointments data: {str(e)}")
        messages.error(request, "An error occurred while fetching appointments data.")

    # Prepare the context for rendering the template
    context = {
        'username': username,
        'appointments': appointments_list,
    }

    # Render the template with the context
    return render(request, 'dashboard/almoner/appointmentmanagement.html', context)
    








# View a Specific Appointment
def view_appointment(request, appointment_id):
    if 'user_id' not in request.session:  # Ensure the user is logged in
        return redirect('login')

    # Query the database for the specific appointment details
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                a.appointment_id, 
                a.appointment_date, 
                a.reason_for_appointment, 
                a.patient_id,
                p.full_name, 
                p.date_of_birth, 
                p.age, 
                p.gender, 
                p.address, 
                p.phone_number, 
                p.email
            FROM 
                appointment a
            JOIN 
                patients p 
            ON 
                a.patient_id = p.patient_id
            WHERE 
                a.appointment_id = %s
        """, [appointment_id])
        appointment = cursor.fetchone()

    # Handle case when appointment is not found
    if not appointment:
        return HttpResponse("Appointment not found", status=404)

    # Map the result to a dictionary for the template
    appointment_details = {
        'appointment_id': appointment[0],
        'appointment_date': appointment[1],
        'reason_for_appointment': appointment[2],
        'patient_id': appointment[3],
        'patient_full_name': appointment[4],
        'patient_date_of_birth': appointment[5],
        'patient_age': appointment[6],
        'patient_gender': appointment[7],
        'patient_address': appointment[8],
        'patient_phone_number': appointment[9],
        'patient_email': appointment[10],
    }

    # Pass the appointment details to the template
    context = {
        'appointment': appointment_details,
    }

    return render(request, 'dashboard/almoner/view_appointment.html', context)





#________________________________________      Nurse            _______________________________________________________________
 

def base_nurse(request):
    return render(request, 'dashboard/nurse/base_nurse.html')



def patient_screening_list(request):
    # Initialize the screenings list
    screenings_list = []

    # Check if the user is logged in
    if 'user_id' not in request.session:
        return redirect('login')

    # Get the username from the session, defaulting to 'Guest'
    username = request.session.get('username', 'Guest')

    try:
        # Fetch screenings data from the database
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    s.screening_id, 
                    p.full_name,  
                    s.height, 
                    s.weight, 
                    s.temperature, 
                    s.blood_pressure, 
                    s.symptoms, 
                    s.complaints, 
                    s.screening_date,
                    s.patient_id
                FROM 
                    screening s
                JOIN 
                    patients p 
                ON 
                    s.patient_id = p.patient_id
                ORDER BY 
                    s.screening_date DESC
                """
            )
            screenings_data = cursor.fetchall()

        # Handle the case where no screenings are found
        if not screenings_data:
            raise ValueError("No screenings found in the database.")

        # Transform the data into a list of dictionaries
        screenings_list = [
            {
                'screening_id': row[0],
                'patient_name': row[1] or "Unknown",  # Default to "Unknown" if NULL
                'height': row[2] or "N/A",           # Default to "N/A" if NULL
                'weight': row[3] or "N/A",           # Default to "N/A" if NULL
                'temperature': row[4] or "N/A",      # Default to "N/A" if NULL
                'blood_pressure': row[5] or "N/A",   # Default to "N/A" if NULL
                'symptoms': row[6] or "None",        # Default to "None" if NULL
                'complaints': row[7] or "None",      # Default to "None" if NULL
                'screening_date': row[8],
                'patient_id': row[9]             # Assume this field is not NULL
            }
            for row in screenings_data
        ]

    except ValueError as ve:
        # Handle specific case of no screenings found
        messages.warning(request, str(ve))
    except Exception as e:
        # Log unexpected errors and display an error message to the user
        print(f"Error while fetching screenings data: {str(e)}")
        messages.error(request, "An error occurred while fetching screenings data.")

    # Prepare the context for rendering the template
    context = {
        'username': username,
        'screenings': screenings_list,
    }

    # Render the template with the context
    return render(request, 'dashboard/nurse/patientscreeningmanagement.html', context)






def search_patient_screened(request):
    # Get the search term from the GET request
    search_term = request.GET.get('search_patient_screened', '').strip()

    patient_data = None
    patients = None

    if search_term:
        # Check if the search term is a valid number (Patient ID) or a name
        try:
            search_patient_id = int(search_term)
            # Searching by Patient ID (raw SQL query)
            with connection.cursor() as cursor:
                cursor.execute("""
                SELECT p.*
                FROM patients p
                JOIN visit v ON p.patient_id = v.patient_id
                WHERE v.status = 'incompleted'
                AND p.patient_id = %s;  
                """, [search_patient_id])
                patients = cursor.fetchall()
        except ValueError:
            # If it's not a number, search by name (raw SQL query)
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM patients WHERE full_name LIKE %s
                """, [f"%{search_term}%"])
                patients = cursor.fetchall()

        if patients:
            patient_data = {
                'patient_id': patients[0][0],  # Adjust index based on actual table schema
                'full_name': patients[0][1],   # Adjust index based on actual table schema
            }

            messages.success(request, "Patient found.")
        else:
            messages.error(request, "No patient found with that ID or name or patient has not meet almoner.")
    else:
        messages.error(request, "Please enter a search term.")

    # Pass the patient data to the template
    return render(request, 'dashboard/nurse/register_patient_screened.html', {
        'patient_data': patient_data,
        'search_patient_screened': search_term
    })

def register_patient_screened(request, patient_id=None):
    # Check if the user is logged in
    if 'user_id' not in request.session:
        return redirect('login')

    # Get the logged-in user's details from the session
    username = request.session.get('username', 'Guest')
    user_id = request.session.get('user_id')

    # Initialize patient details
    patient = None

    # Fetch patient details if patient_id is provided
    if patient_id:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT patient_id, full_name
                FROM patients
                WHERE patient_id = %s
            """, [patient_id])
            result = cursor.fetchone()
            if result:
                patient = {
                    'patient_id': result[0],
                    'full_name': result[1]
                }
            else:
                messages.error(request, "Patient not found.")
                return redirect('search_patient_screened')

    # Handle form submission for registering the visit
    if request.method == 'POST':
        height = request.POST.get('height')
        weight = request.POST.get('weight')
        temperature = request.POST.get('temperature')
        blood_pressure = request.POST.get('blood_pressure')
        symptoms = request.POST.get('symptoms')
        complaints = request.POST.get('complaints')

        # Check if patient details and form fields are provided
        if patient and height and weight and temperature and blood_pressure and symptoms and complaints:
            try:
                with connection.cursor() as cursor:
                    # Insert patient data into the screening table
                    cursor.execute("""
                    INSERT INTO screening (patient_id, height, weight, temperature, blood_pressure, symptoms, complaints, registered_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING screening_id;
                    """, [patient['patient_id'], height, weight, temperature, blood_pressure, symptoms, complaints, user_id])

                    # Fetch the screening_id from the returned row
                    result = cursor.fetchone()
                    if result:
                        screening_id = result[0]
                    else:
                        messages.error(request, "Failed to retrieve screening_id.")
                        return redirect('register_patient_screened', patient_id=patient['patient_id'])

                    # Insert into the AuthorizedPatientForConsultation table
                    cursor.execute("""
                        INSERT INTO AuthorizedPatientForConsultation (patient_id, screening_id, registered_by)
                        VALUES (%s, %s, %s)
                    """, [patient['patient_id'], screening_id, user_id])

                # Success message
                messages.success(request, f"Patient registered successfully in Screening table and AuthorizedPatientForConsultation table by {username}.")
                return redirect('register_patient_screened', patient_id=patient['patient_id'])

            except Exception as e:
                # Handle SQL errors
                messages.error(request, f"An error occurred: {str(e)}")
        else:
            # Error message if fields are missing
            messages.error(request, "Please fill in all the fields.")

    # Pass data to the template
    context = {
        'username': username,
        'user_id': user_id,
        'patient': patient,
    }

    # Render the form template
    return render(request, 'dashboard/nurse/register_patient_screened.html', context)



# def register_patient_screened(request, patient_id=None):
#     # Check if the user is logged in
#     if 'user_id' not in request.session:
#         return redirect('login')

#     # Get the logged-in user's details from the session
#     username = request.session.get('username', 'Guest')
#     user_id = request.session.get('user_id')

#     # Initialize patient details
#     patient = None

#     # Fetch patient details if patient_id is provided
#     if patient_id:
#         with connection.cursor() as cursor:
#             cursor.execute("""
#                 SELECT patient_id, full_name
#                 FROM patients
#                 WHERE patient_id = %s
#             """, [patient_id])
#             result = cursor.fetchone()
#             if result:
#                 patient = {
#                     'patient_id': result[0],
#                     'full_name': result[1]
#                 }
#             else:
#                 messages.error(request, "Patient not found.")
#                 return redirect('search_patient_screened')

#     # Handle form submission for registering the visit
#     if request.method == 'POST':
#         height = request.POST.get('height')
#         weight = request.POST.get('weight')
#         temperature = request.POST.get('temperature')
#         blood_pressure = request.POST.get('blood_pressure')
#         symptoms = request.POST.get('symptoms')
#         complaints = request.POST.get('complaints')

#         if patient and height and weight and temperature and blood_pressure and symptoms and complaints:
#             try:
#                 with connection.cursor() as cursor:
#                     # Insert patient into the screening table
#                     cursor.execute("""
#                         INSERT INTO screening (patient_id, height,weight, blood_pressure, symptoms, complaints, registered_by)
#                         VALUES (%s, %s, %s,%s, %s, %s, %s)
#                     """, [patient['patient_id'], height, weight, blood_pressure, symptoms, complaints, user_id])

#                 # Success message
#                 messages.success(request, f"Patient  registered successfully in complaints table by {username}.")
#                 return redirect('register_patient_screened', patient_id=patient['patient_id'])
#             except Exception as e:
#                 # Handle SQL errors
#                 messages.error(request, f"An error occurred: {str(e)}")
#         else:
#             # Error message if fields are missing
#             messages.error(request, "Please fill in all the fields.")

#     # Pass data to the template
#     context = {
#         'username': username,
#         'user_id': user_id,
#         'patient': patient,
#     }

#     # Render the form template
#     return render(request, 'dashboard/nurse/register_patient_screened.html', context)





# View a Specific Patient
def view_patient_screened(request, patient_id):
    if 'user_id' not in request.session:  # Ensure the user is logged in
        return redirect('login')

    # Query the database for the specific patient's details from the screening table
    with connection.cursor() as cursor:
        cursor.execute("""
    SELECT s.screening_id, s.patient_id, s.height, s.weight, s.temperature,
           s.blood_pressure, s.symptoms, s.complaints, s.screening_date, p.full_name, p.date_of_birth, p.age, p.address, p.phone_number, p.email
    FROM screening s
    JOIN patients p ON s.patient_id = p.patient_id
    WHERE s.patient_id = %s
""", [patient_id])
        screening = cursor.fetchone()

    # Handle case when patient is not found in the screening table
    if not screening:
        return HttpResponse("Patient not found", status=404)

    # Map the result to a dictionary for the template
    screening_details = {
        'screening_id': screening[0],
        'patient_id': screening[1],
        'height': screening[2],
        'weight': screening[3],
        'temperature': screening[4],
        'blood_pressure': screening[5],
        'symptoms': screening[6],
        'complaints': screening[7],
        'screening_date': screening[8],
        'patient_name': screening[9], 
        
        'date_of_birth': screening[10],
        'age': screening[11],
        'address': screening[12],
        'phone_number': screening[13],
        'email': screening[14],  # Ensure this is returned properly
    }

    # Pass the patient details to the template
    context = {
        'screening': screening_details,
    }
    return render(request, 'dashboard/nurse/view_patient_screened.html', context)




# def edit_patient_screened(request, screening_id):
#     if 'user_id' not in request.session:
#         return redirect('login')

#     username = request.session.get('username')
#     user_id = request.session.get('user_id')

#     try:
#         with connection.cursor() as cursor:
#             if request.method == 'POST':
#                 height = request.POST.get('height')
#                 weight = request.POST.get('weight')
#                 temperature = request.POST.get('temperature')
#                 blood_pressure = request.POST.get('blood_pressure')
#                 symptoms = request.POST.get('symptoms')
#                 complaints = request.POST.get('complaints')

#                 # Ensure the values are not None or empty before updating
#                 if all([height, weight, temperature, blood_pressure, symptoms, complaints]):
#                     cursor.execute("""
#                         UPDATE screening
#                         SET height = %s, weight = %s, temperature = %s, blood_pressure = %s, symptoms = %s, complaints = %s
#                         WHERE screening_id = %s
#                     """, [height, weight, temperature, blood_pressure, symptoms, complaints, patient_id])

#                     # Commit the transaction
#                     transaction.commit()

#                     messages.success(request, 'Patient Screening updated successfully!')
#                     return redirect('patientscreeningmanagement')
#                 else:
#                     messages.error(request, 'All fields are required.')

#             # Fetch existing screening details for the patient
#             cursor.execute("""
#                 SELECT height, weight, temperature, blood_pressure, symptoms, complaints
#                 FROM screening
#                 WHERE patient_id = %s
#             """, [patient_id])
#             screening_data = cursor.fetchone()

#             if not screening_data:
#                 messages.error(request, 'Patient Screening not found.')
#                 return redirect('patientscreeningmanagement')

#             # Map the screening data to a dictionary
#             screening = {
#                 'height': screening_data[0],
#                 'weight': screening_data[1],
#                 'temperature': screening_data[2],
#                 'blood_pressure': screening_data[3],
#                 'symptoms': screening_data[4],
#                 'complaints': screening_data[5],
#             }

#             context = {
#                 'screening': screening,
#                 'username': username,
#                 'user_id': user_id,
#             }
#             return render(request, 'dashboard/nurse/edit_patient_screened.html', context)

#     except Exception as e:
#         messages.error(request, f"Error: {str(e)}")
#     return redirect('patientscreeningmanagement')

def edit_patient_screened(request, screening_id):
    if 'user_id' not in request.session:
        return redirect('login')

    username = request.session.get('username')
    user_id = request.session.get('user_id')

    try:
        with connection.cursor() as cursor:
            if request.method == 'POST':
                height = request.POST.get('height')
                weight = request.POST.get('weight')
                temperature = request.POST.get('temperature')
                blood_pressure = request.POST.get('blood_pressure')
                symptoms = request.POST.get('symptoms')
                complaints = request.POST.get('complaints')

                # Ensure the values are not None or empty before updating
                if all([height, weight, temperature, blood_pressure, symptoms, complaints]):
                    cursor.execute("""
                        UPDATE screening
                        SET height = %s, weight = %s, temperature = %s, blood_pressure = %s, symptoms = %s, complaints = %s
                        WHERE screening_id = %s
                    """, [height, weight, temperature, blood_pressure, symptoms, complaints, screening_id])

                    # Commit the transaction
                    # transaction.commit()
  
                    messages.success(request, 'Patient Screening updated successfully!')
                    return redirect('patientscreeningmanagement')
                else:
                    messages.error(request, 'All fields are required.')

            # Fetch existing screening details using the screening_id
            cursor.execute("""
                SELECT height, weight, temperature, blood_pressure, symptoms, complaints
                FROM screening
                WHERE screening_id = %s
            """, [screening_id])
            screening_data = cursor.fetchone()

            if not screening_data:
                messages.error(request, 'Patient Screening not found.')
                return redirect('patientscreeningmanagement')

            # Map the screening data to a dictionary
            screening = {
                'height': screening_data[0],
                'weight': screening_data[1],
                'temperature': screening_data[2],
                'blood_pressure': screening_data[3],
                'symptoms': screening_data[4],
                'complaints': screening_data[5],
            }

            context = {
                'screening': screening,
                'username': username,
                'user_id': user_id,
            }
            return render(request, 'dashboard/nurse/edit_patient_screened.html', context)

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
    return redirect('patientscreeningmanagement')

###################################################################################################################################

                                                      # Doctor

########################################################################################################################################




def base_doctor(request):
    return render(request, 'dashboard/doctor/base_doctor.html')


def Consultation(request):
    consultation_list = []

    if 'user_id' not in request.session:
        return redirect('login')

    username = request.session.get('username', 'Guest')

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    c.id, 
                    p.patient_id,  
                    p.full_name,   
                    c.diagnosis, 
                    c.treatment, 
                    c.prescription,
                    c.registered_by,
                    c.created_at
                FROM 
                    consultation c
                JOIN 
                    patients p 
                ON 
                    c.patient_id = p.patient_id
                ORDER BY 
                    c.created_at DESC  -- Order by date in descending order
                """
            )
            consultation_data = cursor.fetchall()

        if not consultation_data:
            raise ValueError("No consultation found in the database.")

        consultation_list = [
            {
                'id': row[0],
                'patient_id': row[1] or "Unknown",
                'full_name': row[2] or "N/A",
                'diagnosis': row[3] or "N/A",
                'treatment': row[4] or "N/A",
                'prescription': row[5] or "N/A",
                'registered_by': row[6] or "N/A",
                'created_at': row[7].strftime('%Y-%m-%d')  # Format the date
    
            }
            for row in consultation_data
        ]

    except ValueError as ve:
        messages.warning(request, str(ve))
    except Exception as e:
        print(f"Error while fetching consultation data: {str(e)}")
        messages.error(request, "An error occurred while fetching consultation data.")

    

    context = {
        'username': username,
        'consultations': consultation_list,  # Ensure this is 'consultations'
    }

    return render(request, 'dashboard/doctor/patient_consultation_management.html', context)





# def search_patient_consulted(request):
#     # Get the search term from the GET request
#     search_term = request.GET.get('search_patient_consulted', '').strip()

#     patient_data = None
#     patients = None

#     if search_term:
#         # Check if the search term is a valid number (Patient ID) or a name
#         try:
#             search_patient_id = int(search_term)
#             # Searching by Patient ID (raw SQL query)
#             with connection.cursor() as cursor:
#                 cursor.execute("""
#                 SELECT * FROM patients WHERE patient_id = %s   
#                 """, [search_patient_id])
#                 patients = cursor.fetchall()
#         except ValueError:
#             # If it's not a number, search by name (raw SQL query)
#             with connection.cursor() as cursor:
#                 cursor.execute("""
#                     SELECT * FROM patients WHERE full_name LIKE %s
#                 """, [f"%{search_term}%"])
#                 patients = cursor.fetchall()

#         if patients:
#             patient_data = {
#                 'patient_id': patients[0][0],  # Adjust index based on actual table schema
#                 'full_name': patients[0][1],   # Adjust index based on actual table schema
#             }

#             messages.success(request, "Patient found.")
#         else:
#             messages.error(request, "No patient found with that ID or name or patient has not meet almoner.")
#     else:
#         messages.error(request, "Please enter a search term.")

#     # Pass the patient data to the template
#     return render(request, 'dashboard/doctor/register_patient_consulted.html', {
#         'patient_data': patient_data,
#         'search_patient_consulted': search_term
#     })
def search_patient_consulted(request):
    # Get the search term from the GET request
    search_term = request.GET.get('search_patient_consulted', '').strip()

    patient_data = None
    screening_data = None
    consultation_date = None

    # Only perform search if a search term is provided
    if search_term:
        try:
            # Handle cases where search term might be "Full Name (ID: ID_NUMBER)"
            if '(' in search_term and 'ID:' in search_term:
                name_part = search_term.split('(')[0].strip()
                id_part = search_term.split('ID:')[1].strip(' )')

                if id_part.isdigit():
                    search_patient_id = int(id_part)
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT * FROM patients 
                            WHERE patient_id = %s AND LOWER(full_name) = LOWER(%s)
                        """, [search_patient_id, name_part])
                        patient = cursor.fetchone()
                else:
                    messages.error(request, "Invalid ID format in the search term.")
                    return render(request, 'dashboard/doctor/register_patient_consulted.html', {
                        'patient_data': None,
                        'screening_data': None,
                        'consultation_date': None,
                        'search_patient_consulted': search_term,
                    })
            elif search_term.isdigit():
                # Search by ID
                search_patient_id = int(search_term)
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM patients WHERE patient_id = %s
                    """, [search_patient_id])
                    patient = cursor.fetchone()
            else:
                # Search by full name
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM patients WHERE LOWER(full_name) LIKE LOWER(%s)
                    """, [f"%{search_term}%"])
                    patients = cursor.fetchall()

                if patients:
                    patient = patients[0]
                else:
                    patient = None

            if patient:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM screening WHERE patient_id = %s
                    """, [patient[0]])
                    screening = cursor.fetchone()

                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT created_at FROM consultation WHERE patient_id = %s
                    """, [patient[0]])
                    consultation = cursor.fetchone()

                patient_data = {
                    'patient_id': patient[0],
                    'full_name': patient[1],
                }

                if screening:
                    screening_data = {
                        'height': screening[2],
                        'weight': screening[3],
                        'temperature': screening[4],
                        'blood_pressure': screening[5],
                        'symptoms': screening[6],
                        'complaints': screening[7],
                    }

                if consultation:
                    consultation_date = consultation[0]
                    messages.info(
                        request,
                        f"The patient was already consulted on {consultation_date.strftime('%Y-%m-%d')}."
                    )
            else:
                messages.error(request, "No patient found with the given search term.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    else:
        # If no search term, skip the search and render the page for registration
        messages.info(request, "No search performed. Ready for patient registration.")

    return render(request, 'dashboard/doctor/register_patient_consulted.html', {
        'patient_data': patient_data,
        'screening_data': screening_data,
        'consultation_date': consultation_date,
        'search_patient_consulted': search_term,
    })





def register_patient_consulted(request, patient_id=None):
    if 'user_id' not in request.session:
        return redirect('login')
    
    username = request.session.get('username', 'Guest')
    user_id = request.session.get('user_id')
    patient = None
    screenings = []
    consultation_data = None

    # Fetch all authorized patients with incomplete status
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT apc.screening_id, apc.patient_id, p.full_name 
            FROM AuthorizedPatientForConsultation apc
            INNER JOIN patients p ON apc.patient_id = p.patient_id
            WHERE apc.status = 'incomplete'
            ORDER BY p.full_name
        """)
        authorized_patients = [
            {
                'screening_id': row[0],
                'patient_id': row[1],
                'full_name': row[2]
            } for row in cursor.fetchall()
        ]

    # Fetch patient details and screening data if patient_id is provided
    if patient_id:
        with connection.cursor() as cursor:
            # Fetch patient details
            cursor.execute("""
                SELECT patient_id, full_name
                FROM patients
                WHERE patient_id = %s
            """, [patient_id])
            result = cursor.fetchone()
            if result:
                patient = {
                    'patient_id': result[0],
                    'full_name': result[1]
                }
            else:
                messages.error(request, "Patient not found.")
                return redirect('register_patient_consulted')

            # Fetch screening details for the patient
            cursor.execute("""
                SELECT screening_date, height, weight, blood_pressure, temperature, symptoms, complaints
                FROM screening
                WHERE patient_id = %s
            """, [patient_id])
            screening_results = cursor.fetchall()

            # Format screening details into a dictionary (just one record, if any)
            if screening_results:
                screenings = {
                    'screening_date': screening_results[0][0],
                    'height': screening_results[0][1],
                    'weight': screening_results[0][2],
                    'blood_pressure': screening_results[0][3],
                    'temperature': screening_results[0][4],
                    'symptoms': screening_results[0][5],
                    'complaints': screening_results[0][6],
                }

            if not screenings:
                messages.info(request, "No screening details found for this patient.")

            # Fetch existing consultation data (if available)
            cursor.execute("""
                SELECT diagnosis, treatment, prescription
                FROM consultation
                WHERE patient_id = %s
                ORDER BY created_at DESC LIMIT 1
            """, [patient_id])
            consultation_result = cursor.fetchone()

            if consultation_result:
                consultation_data = {
                    'diagnosis': consultation_result[0] or 'No Diagnosis Available',
                    'treatment': consultation_result[1] or 'No Treatment Available',
                    'prescription': consultation_result[2] or 'No Prescription Available',
                }

    # Handle form submission for registering the visit
    if request.method == 'POST':
        diagnosis = request.POST.get('diagnosis')
        treatment = request.POST.get('treatment')
        prescription = request.POST.get('prescription')

        if patient and diagnosis and treatment and prescription:
            try:
                with connection.cursor() as cursor:
                    # Check if consultation already exists (to update or insert)
                    cursor.execute("""
                        SELECT id
                        FROM consultation
                        WHERE patient_id = %s
                    """, [patient['patient_id']])
                    existing_consultation = cursor.fetchone()

                    if existing_consultation:
                        # Update the existing consultation
                        cursor.execute("""
                            UPDATE consultation
                            SET diagnosis = %s, treatment = %s, prescription = %s, updated_at = NOW()
                            WHERE id = %s
                        """, [diagnosis, treatment, prescription, existing_consultation[0]])
                    else:
                        # Insert a new consultation
                        cursor.execute("""
                            INSERT INTO consultation (patient_id, diagnosis, treatment, prescription, registered_by, created_at)
                            VALUES (%s, %s, %s, %s, %s, NOW())
                        """, [patient['patient_id'], diagnosis, treatment, prescription, user_id])

                    # Update the status in AuthorizedPatientForConsultation table to 'completed'
                    cursor.execute("""
                        UPDATE AuthorizedPatientForConsultation
                        SET status = 'completed'
                        WHERE patient_id = %s AND status = 'incomplete'
                    """, [patient['patient_id']])

                # Success message
                messages.success(request, f"Consultation for {patient['full_name']} has been saved successfully and status updated to 'completed'.")
                return redirect('register_patient_consulted', patient_id=patient['patient_id'])
            except Exception as e:
                # Handle SQL errors
                messages.error(request, f"An error occurred: {str(e)}")
        else:
            # Error message if fields are missing
            messages.error(request, "Please fill in all the fields.")

    # Pass data to the template
    context = {
        'username': username,
        'user_id': user_id,
        'patient': patient,
        'screenings': screenings,  # Pass screening data to the template
        'consultation_data': consultation_data,  # Pass existing consultation data to the template
        'authorized_patients': json.dumps(authorized_patients, cls=DjangoJSONEncoder)
    }

    # Render the form template
    return render(request, 'dashboard/doctor/register_patient_consulted.html', context)


# def register_patient_consulted(request, patient_id=None):
#     # Check if the user is logged in
#     if 'user_id' not in request.session:
#         return redirect('login')

#     # Get the logged-in user's details from the session
#     username = request.session.get('username', 'Guest')
#     user_id = request.session.get('user_id')

#     # Initialize patient details, screening data, and consultation data
#     patient = None
#     screenings = []
#     consultation_data = None

#     # Fetch patient details and screening data if patient_id is provided
#     if patient_id:
#         with connection.cursor() as cursor:
#             # Fetch patient details
#             cursor.execute("""
#                 SELECT patient_id, full_name
#                 FROM patients
#                 WHERE patient_id = %s
#             """, [patient_id])
#             result = cursor.fetchone()
#             if result:
#                 patient = {
#                     'patient_id': result[0],
#                     'full_name': result[1]
#                 }
#             else:
#                 messages.error(request, "Patient not found.")
#                 return redirect('register_patient_consulted')

#             # Fetch screening details for the patient
#             cursor.execute("""
#                 SELECT screening_date, height, weight, blood_pressure, temperature, symptoms, complaints
#                 FROM screening
#                 WHERE patient_id = %s
#             """, [patient_id])
#             screening_results = cursor.fetchall()

#             # Format screening details into a dictionary (just one record, if any)
#             if screening_results:
#                 screenings = {
#                     'screening_date': screening_results[0][0],
#                     'height': screening_results[0][1],
#                     'weight': screening_results[0][2],
#                     'blood_pressure': screening_results[0][3],
#                     'temperature': screening_results[0][4],
#                     'symptoms': screening_results[0][5],
#                     'complaints': screening_results[0][6],
#                 }

#             if not screenings:
#                 messages.info(request, "No screening details found for this patient.")

#             # Fetch existing consultation data (if available)
#             cursor.execute("""
#                 SELECT diagnosis, treatment, prescription
#                 FROM consultation
#                 WHERE patient_id = %s
#                 ORDER BY created_at DESC LIMIT 1
#             """, [patient_id])
#             consultation_result = cursor.fetchone()

#             if consultation_result:
#                 consultation_data = {
#                     'diagnosis': consultation_result[0] or 'No Diagnosis Available',
#                     'treatment': consultation_result[1] or 'No Treatment Available',
#                     'prescription': consultation_result[2] or 'No Prescription Available',
#                 }

#     # Handle form submission for registering the visit
#     if request.method == 'POST':
#         diagnosis = request.POST.get('diagnosis')
#         treatment = request.POST.get('treatment')
#         prescription = request.POST.get('prescription')

#         if patient and diagnosis and treatment and prescription:
#             try:
#                 with connection.cursor() as cursor:
#                     # Check if consultation already exists (to update or insert)
#                     cursor.execute("""
#                         SELECT id
#                         FROM consultation
#                         WHERE patient_id = %s
#                     """, [patient['patient_id']])
#                     existing_consultation = cursor.fetchone()

#                     if existing_consultation:
#                         # Update the existing consultation
#                         cursor.execute("""
#                             UPDATE consultation
#                             SET diagnosis = %s, treatment = %s, prescription = %s, updated_at = NOW()
#                             WHERE id = %s
#                         """, [diagnosis, treatment, prescription, existing_consultation[0]])
#                     else:
#                         # Insert a new consultation
#                         cursor.execute("""
#                             INSERT INTO consultation (patient_id, diagnosis, treatment, prescription, registered_by, created_at)
#                             VALUES (%s, %s, %s, %s, %s, NOW())
#                         """, [patient['patient_id'], diagnosis, treatment, prescription, user_id])

#                 # Success message
#                 messages.success(request, f"Consultation for {patient['full_name']} has been saved successfully.")
#                 return redirect('register_patient_consulted', patient_id=patient['patient_id'])
#             except Exception as e:
#                 # Handle SQL errors
#                 messages.error(request, f"An error occurred: {str(e)}")
#         else:
#             # Error message if fields are missing
#             messages.error(request, "Please fill in all the fields.")

#     # Pass data to the template
#     context = {
#         'username': username,
#         'user_id': user_id,
#         'patient': patient,
#         'screenings': screenings,  # Pass screening data to the template
#         'consultation_data': consultation_data,  # Pass existing consultation data to the template
#     }

#     # Render the form template
#     return render(request, 'dashboard/doctor/register_patient_consulted.html', context)











def view_patient_consultation(request, patient_id=None):
    # Check if the user is logged in
    if 'user_id' not in request.session:
        return redirect('login')

    # Get the logged-in user's details from the session
    username = request.session.get('username', 'Guest')
    user_id = request.session.get('user_id')

    # Initialize patient details, screening data, and consultation data
    patient = None
    screenings = {}
    consultation_data = None

    # Fetch patient details, consultation, and screening data if patient_id is provided
    if patient_id:
        with connection.cursor() as cursor:
            # Fetch patient details
            cursor.execute("""
                SELECT patient_id, full_name
                FROM patients
                WHERE patient_id = %s
            """, [patient_id])
            result = cursor.fetchone()
            if result:
                patient = {
                    'patient_id': result[0],
                    'full_name': result[1]
                }
            else:
                messages.error(request, "Patient not found.")
                return redirect('view_patient_consultation')

            # Fetch screening details (vital signs) for the patient
            cursor.execute("""
                SELECT screening_date, height, weight, blood_pressure, temperature, symptoms, complaints
                FROM screening
                WHERE patient_id = %s
            """, [patient_id])
            screening_results = cursor.fetchall()

            # Format screening details (vital signs) into a dictionary (just one record, if any)
            if screening_results:
                screenings = {
                    'screening_date': screening_results[0][0],
                    'height': screening_results[0][1],
                    'weight': screening_results[0][2],
                    'blood_pressure': screening_results[0][3],
                    'temperature': screening_results[0][4],
                    'symptoms': screening_results[0][5],
                    'complaints': screening_results[0][6],
                }

            if not screenings:
                messages.info(request, "No screening details found for this patient.")

            # Fetch the latest consultation data (if available)
            cursor.execute("""
                SELECT diagnosis, treatment, prescription
                FROM consultation
                WHERE patient_id = %s
                ORDER BY created_at DESC LIMIT 1
            """, [patient_id])
            consultation_result = cursor.fetchone()

            if consultation_result:
                consultation_data = {
                    'diagnosis': consultation_result[0] or 'No Diagnosis Available',
                    'treatment': consultation_result[1] or 'No Treatment Available',
                    'prescription': consultation_result[2] or 'No Prescription Available',
                }

    else:
        messages.error(request, "No patient ID provided.")
        return redirect('view_patients_list')  # Redirect to a list of patients or an appropriate view.

    # Pass data to the template
    context = {
        'username': username,
        'user_id': user_id,
        'patient': patient,
        'screenings': screenings,  # Pass vital signs data to the template
        'consultation_data': consultation_data,  # Pass consultation data to the template
    }

    # Render the consultation view template
    return render(request, 'dashboard/doctor/view_patient_consultation.html', context)







# def register_patient_consulted(request, patient_id=None):
#     # Check if the user is logged in
#     if 'user_id' not in request.session:
#         return redirect('login')

#     # Get the logged-in user's details from the session
#     username = request.session.get('username', 'Guest')
#     user_id = request.session.get('user_id')

#     # Initialize patient details
#     patient = None

#     # Fetch patient details if patient_id is provided
#     if patient_id:
#         with connection.cursor() as cursor:
#             cursor.execute("""
#                 SELECT patient_id, full_name
#                 FROM patients
#                 WHERE patient_id = %s
#             """, [patient_id])
#             result = cursor.fetchone()
#             if result:
#                 patient = {
#                     'patient_id': result[0],
#                     'full_name': result[1]
#                 }
#             else:
#                 messages.error(request, "Patient not found.")
#                 return redirect('register_patient_consulted')

#     # Handle form submission for registering the visit
#     if request.method == 'POST':
#         diagnosis = request.POST.get('diagnosis')
#         treatment = request.POST.get('treatment')
#         prescription = request.POST.get('prescription')
       

#         if patient and diagnosis and treatment and prescription :
#             try:
#                 with connection.cursor() as cursor:
#                     # Insert patient into the screening table
#                     cursor.execute("""
#                         INSERT INTO consultation (patient_id, diagnosis,treatment, prescription, registered_by)
#                         VALUES (%s, %s, %s,%s, %s)
#                     """, [patient['patient_id'], diagnosis,treatment, prescription, user_id])

#                 # Success message
#                 messages.success(request, f"Patient  registered successfully in consultation table by {username}.")
#                 return redirect('register_patient_consulted', patient_id=patient['patient_id'])
#             except Exception as e:
#                 # Handle SQL errors
#                 messages.error(request, f"An error occurred: {str(e)}")
#         else:
#             # Error message if fields are missing
#             messages.error(request, "Please fill in all the fields.")

#     # Pass data to the template
#     context = {
#         'username': username,
#         'user_id': user_id,
#         'patient': patient,
#     }

#     # Render the form template
#     return render(request, 'dashboard/doctor/register_patient_consulted.html', context)

         


def edit_patient_consulted(request, id):
    if 'user_id' not in request.session:
        return redirect('login')

    username = request.session.get('username')
    user_id = request.session.get('user_id')

    try:
        with connection.cursor() as cursor:
            if request.method == 'POST':
                diagnosis = request.POST.get('diagnosis')
                treatment = request.POST.get('treatment')
                prescription = request.POST.get('prescription')


                # Ensure the values are not None or empty before updating
                if all([diagnosis, treatment, prescription]):
                    cursor.execute("""
                        UPDATE consultationSarah Wilson
                        SET diagnosis = %s, treatment = %s, prescription = %s
                        WHERE id = %s
                    """, [diagnosis, treatment, prescription])

                    # Commit the transaction
                    # transaction.commit()
  
                    messages.success(request, 'Patient Consultation updated successfully!')
                    return redirect('patient_consultation_management')
                else:
                    messages.error(request, 'All fields are required.')

            # Fetch existing Consultation details using the screening_id
            cursor.execute("""
                SELECT diagnosis, treatment, prescription
                FROM consultation
                WHERE id = %s
            """, [id])
            consultation_data = cursor.fetchone()

            if not consultation_data:
                messages.error(request, 'Patient consultation not found.')
                return redirect('patient_consultation_management')

            # Map the screening data to a dictionary
            consultation = {
                'diagnosis': consultation_data[0],
                'treatment': consultation_data[1],
                'prescription': consultation_data[2],

            }

            context = {
                'consultation': consultation,
                'username': username,
                'user_id': user_id,
            }
            return render(request, 'dashboard/doctor/edit_patient_consulted.html', context)

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
    return redirect('patient_consultation_management')













#############################################           Add patient                 #################################################################
def new_patient_list(request):
    if 'user_id' not in request.session:
        return redirect('login')
    
    username = request.session.get('username', 'Guest')
    user_id = request.session.get('user_id')

    if request.method == 'POST':
        try:
            # Capture form data
            full_name = request.POST.get('full_name')
            date_of_birth = request.POST.get('date_of_birth')
            age = int(request.POST.get('age', 0))
            gender = request.POST.get('gender')
            address = request.POST.get('address')
            phone_number = request.POST.get('phone_number', '')
            email = request.POST.get('email', '')
            dependent_name = request.POST.get('dependent_name')
            dependent_contact = request.POST.get('dependent_contact')
            insurance = request.POST.get('insurance')
            reason_for_visit = request.POST.get('reason_for_visit')
            
            # Capture the almoner who is registering the patient
            registered_by = user_id

            with connection.cursor() as cursor:
                # Insert new patient and get the patient_id
                cursor.execute("""
                    INSERT INTO patients 
                    (full_name, date_of_birth, age, gender, address, phone_number, email, dependent_name, dependent_contact, insurance, registered_by) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING patient_id
                """, [full_name, date_of_birth, age, gender, address, phone_number, email, dependent_name, dependent_contact, insurance, registered_by])

                # Get the patient_id of the newly inserted patient
                patient_id = cursor.fetchone()[0]

                # Get the current timestamp
                current_time = datetime.now()

                # Insert the reason for visit into the visit table
                cursor.execute("""
                    INSERT INTO visit (patient_id, reason_for_visit, visit_date, registered_by) 
                    VALUES (%s, %s, %s , %s)
                """, [patient_id, reason_for_visit, current_time, registered_by])

                # Commit the transaction
                connection.commit()

                # Success message
                messages.success(request, 'New Patient registered successfully!')
                return redirect('register_new_patient')

        except Exception as e:
            # Rollback the transaction in case of error
            connection.rollback()
            messages.error(request, f'Error registering new patient: {str(e)}')
            return redirect('register_new_patient')

    # Pass username to the template for pre-filling the 'registered_by' field
    context = {'username': username, 'user_id': user_id}
    return render(request, 'dashboard/almoner/register_new_patient.html', context)



# def new_patient_list(request):
#     if 'user_id' not in request.session:
#         return redirect('login')
    
#     username = request.session.get('username')  # Default to 'Guest' if not logged in
#     user_id = request.session.get('user_id') 
    
#     if request.method == 'POST':
#         try:
#             # Capture form data
#             full_name = request.POST.get('full_name')
#             date_of_birth = request.POST.get('date_of_birth')
#             age = int(request.POST.get('age', 0))  # Convert to integer
#             gender = request.POST.get('gender')
#             address = request.POST.get('address')
#             phone_number = request.POST.get('phone_number', '')
#             email = request.POST.get('email', '')
#             dependent_name = request.POST.get('dependent_name')
#             dependent_contact = request.POST.get('dependent_contact')
#             insurance = request.POST.get('insurance')
#             reason_for_visit = request.POST.get('reason_for_visit')

#         #    1- # put the one for reason of visit

#             # Capture the almoner who is registering the patient

#             registered_by = request.session.get('user_id')

#             with connection.cursor() as cursor:
#                 # Insert new patient
#                 cursor.execute("""
#                     INSERT INTO patients 
#                     (full_name, date_of_birth, age, gender, address, phone_number, email, dependent_name, dependent_contact, insurance, registered_by) 
#                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#                 """, [full_name, date_of_birth, age, gender, address, phone_number, email, dependent_name, dependent_contact, insurance, registered_by])
                
#                 connection.commit()
#                 messages.success(request, 'New Patient registered successfully!')
#                 return redirect('register_new_patient')

#         except Exception as e:
#             connection.rollback()
#             messages.error(request, f'Error registering new patient: {str(e)}')
#             return redirect('register_new_patient')




#     # 2 -#select the patient id with this patient name(current patient)

#  # Get the newly inserted patient's ID
#                 cursor.execute("SELECT LAST_INSERT_ID()")
#                 patient_id = cursor.fetchone()[0]

    
# # 3 take the current time using python datetime

# # Get the current timestamp
#                 current_time = datetime.now()
# #    4- #you use that patient id to insert reason of visit in visit table
#                 cursor.execute("""
#                     INSERT INTO visit (patient_id, reason_for_visit, visit_date) 
#                     VALUES (%s, %s, %s)
#                 """, [patient_id, reason_for_visit, current_time])

#                 connection.commit()
#                 messages.success(request, 'New Patient registered successfully!')
#                 return redirect('register_new_patient')
                
#                 except Exception as e:
#                     connection.rollback()
#                     messages.error(request, f'Error registering new patient: {str(e)}')
#                     return redirect('register_new_patient')


#     # Pass username to the template for pre-filling the 'registered_by' field
     
#     context = {'username': username, 'user_id':user_id}
    
#     return render(request, 'dashboard/almoner/register_new_patient.html', context)







def patient_visit_list(request):
    # Check if the user is logged in
    if 'user_id' not in request.session:
        return redirect('login')

    username = request.session.get('username')  # Default to 'Guest' if not logged in
    user_id = request.session.get('user_id')

    patients = []  # Initialize patients list

    if request.method == 'POST':
        if 'search' in request.POST:
            # Handle search functionality
            search_term = request.POST.get('search_term')
            try:
                with connection.cursor() as cursor:
                    # Query to search patients by patient_id or patient_name
                    cursor.execute("""
                    SELECT patient_id, patient_name 
                    FROM patients 
                    WHERE patient_id LIKE %s OR patient_name LIKE %s
                    """, [f"%{search_term}%", f"%{search_term}%"])
                    patients = cursor.fetchall()
            except Exception as e:
                messages.error(request, f'Error searching patients: {str(e)}')

        elif 'register' in request.POST:
            # Handle registration of a new visit
            try:
                patient_id = request.POST.get('patient_id')
                reason_for_visit = request.POST.get('reason_for_visit')
                visit_date = request.POST.get('visit_date')
                registered_by = user_id  # The almoner registering the patient

                with connection.cursor() as cursor:
                    # Insert the visit record into the visit table
                    cursor.execute("""
                    INSERT INTO visit (patient_id, reason_for_visit, visit_date, registered_by) 
                    VALUES (%s, %s, %s, %s)
                    """, [patient_id, reason_for_visit, visit_date, registered_by])

                connection.commit()
                messages.success(request, 'Patient visit registered successfully!')
                return redirect('patient_visit_list')

            except Exception as e:
                connection.rollback()
                messages.error(request, f'Error registering patient visit: {str(e)}')

    else:
        try:
            # Default: Load all patients
            with connection.cursor() as cursor:
                cursor.execute("SELECT patient_id, patient_name FROM patients")
                patients = cursor.fetchall()
        except Exception as e:
            messages.error(request, f'Error loading patient data: {str(e)}')

    # Pass data to the template
    context = {
        'username': username,
        'user_id': user_id,
        'patients': patients,
    }
    return render(request, 'dashboard/almoner/register_patient_visit.html', context)






def search_patient(request):
    # Get the search term from the GET request
    search_term = request.GET.get('search_patient', '').strip()

    patient_data = None
    patients = None

    if search_term:
        # Check if the search term is a valid number (Patient ID) or a name
        try:
            search_patient_id = int(search_term)
            # Searching by Patient ID (raw SQL query)
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM patients WHERE patient_id = %s   
                """, [search_patient_id])
                patients = cursor.fetchall()
        except ValueError:
            # If it's not a number, search by name (raw SQL query)
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM patients WHERE full_name LIKE %s
                """, [f"%{search_term}%"])
                patients = cursor.fetchall()

        if patients:
            patient_data = {
                'patient_id': patients[0][0],  # Adjust index based on actual table schema
                'full_name': patients[0][1],   # Adjust index based on actual table schema
            }
            messages.success(request, "Patient found.")
        else:
            messages.error(request, "No patient found with that ID or name.")
    else:
        messages.error(request, "Please enter a search term.")

    # Pass the patient data to the template
    return render(request, 'dashboard/almoner/register_patient_visit.html', {
        'patient_data': patient_data,
        'search_patient': search_term
    })


def register_patient_visit(request, patient_id=None):
    # Check if the user is logged in
    if 'user_id' not in request.session:
        return redirect('login')

    # Get the logged-in user's details from the session
    username = request.session.get('username', 'Guest')
    user_id = request.session.get('user_id')

    # Initialize patient details
    patient = None

    # Fetch patient details if patient_id is provided
    if patient_id:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT patient_id, full_name
                FROM patients
                WHERE patient_id = %s
            """, [patient_id])
            result = cursor.fetchone()
            if result:
                patient = {
                    'patient_id': result[0],
                    'full_name': result[1]
                }
            else:
                messages.error(request, "Patient not found.")
                return redirect('search_patient')

    # Handle form submission for registering the visit
    if request.method == 'POST':
        reason_for_visit = request.POST.get('reason_for_visit')
        registered_by = user_id

        # Set visit_date to the current date and time
        visit_date = datetime.now()

        # Validate the form data
        if patient and reason_for_visit:
            try:
                # Insert visit into the visit table
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO visit (patient_id, visit_date, reason_for_visit, registered_by)
                        VALUES (%s, %s, %s, %s)
                    """, [patient['patient_id'], visit_date, reason_for_visit, registered_by])

                # Success message
                messages.success(request, f"Patient visit registered successfully by {username}.")
                return redirect('register_patient_visit', patient_id=patient['patient_id'])
            except Exception as e:
                # Handle SQL errors
                messages.error(request, f"An error occurred: {str(e)}")
        else:
            # Error message if any fields are missing
            messages.error(request, "Please fill in all the fields.")

    # Pass data to the template
    context = {
        'username': username,
        'user_id': user_id,
        'patient': patient,
    }

    # Render the form template
    return render(request, 'dashboard/almoner/register_patient_visit.html', context)

##############################################################################################################


# Search Patient Appointment
def search_patient_appointment(request):
    search_term = request.GET.get('search_patient_appointment', '').strip()
    patient_data = None

    if search_term:
        try:
            with connection.cursor() as cursor:
                # Check if the search term is numeric (Patient ID)
                if search_term.isdigit():
                    cursor.execute("SELECT patient_id, full_name FROM patients WHERE patient_id = %s", [search_term])
                else:
                    # Search by name
                    cursor.execute("SELECT patient_id, full_name FROM patients WHERE full_name LIKE %s", [f"%{search_term}%"])

                patient = cursor.fetchone()

            if patient:
                patient_data = {
                    'patient_id': patient[0],
                    'full_name': patient[1],
                }
                messages.success(request, "Patient found.")
            else:
                messages.error(request, "No patient found with the provided ID or name.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    else:
        messages.error(request, "Please enter a search term.")

    return render(request, 'dashboard/almoner/register_patient_appointment.html', {
        'patient_data': patient_data,
        'search_patient_appointment': search_term,
    })





# Register Patient Appointment
def register_patient_appointment(request, patient_id=None):
    if 'user_id' not in request.session:
        return redirect('login')

    # Get user info from session
    username = request.session.get('username', 'Guest')
    user_id = request.session.get('user_id')
    patient = None

    # Retrieve patient information if patient_id is provided
    if patient_id:
        with connection.cursor() as cursor:
            cursor.execute("SELECT patient_id, full_name FROM patients WHERE patient_id = %s ORDER BY appointment_date DESC", [patient_id] )
            result = cursor.fetchone()
            if result:
                patient = {
                    'patient_id': result[0],
                    'full_name': result[1],
                }
            else:
                messages.error(request, "Patient not found.")
                return redirect('search_patient_appointment')

    # Handle form submission
    if request.method == 'POST':
        appointment_date = request.POST.get('appointment_date')
        reason = request.POST.get('reason_for_appointment')

        # Ensure all fields are provided
        if appointment_date and reason:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO appointment (patient_id, appointment_date, registered_by, reason_for_appointment)
                        VALUES (%s, %s, %s, %s)
                    """, [patient_id, appointment_date, user_id, reason])
                
                # Commit the transaction
                messages.success(request, "Appointment registered successfully.")
                return redirect('search_patient_appointment')
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
        else:
            messages.error(request, "All fields are required.")

    # Render the appointment form
    return render(request, 'dashboard/almoner/register_patient_appointment.html', {
        'patient': patient,
        'username': username,
    })


#########################   edit patient            #########################################


# def edit_patient(request, patient_id):
#     if 'user_id' not in request.session:
#         return redirect('login')

#     username = request.session.get('username')
#     user_id = request.session.get('user_id')

#     try:
#         # Fetch patient data to prefill the form
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT * FROM patients WHERE patient_id = %s", [patient_id])
#             patient = cursor.fetchone()

#         if not patient:
#             messages.error(request, "Patient not found.")
#             return redirect('patient_list')  # Redirect to your patient list page

#     except Exception as e:
#         messages.error(request, f"Error fetching patient details: {str(e)}")
#         return redirect('patient_list')

#     if request.method == 'POST':
#         try:
#             # Capture updated form data
#             full_name = request.POST.get('full_name')
#             date_of_birth = request.POST.get('date_of_birth')
#             age = int(request.POST.get('age', 0))
#             gender = request.POST.get('gender')
#             address = request.POST.get('address')
#             phone_number = request.POST.get('phone_number', '')
#             email = request.POST.get('email', '')
#             dependent_name = request.POST.get('dependent_name')
#             dependent_contact = request.POST.get('dependent_contact')
#             insurance = request.POST.get('insurance')

#             with connection.cursor() as cursor:
#                 # Update patient information
#                 cursor.execute("""
#                     UPDATE patients 
#                     SET full_name = %s, date_of_birth = %s, age = %s, gender = %s, address = %s, 
#                         phone_number = %s, email = %s, dependent_name = %s, dependent_contact = %s, insurance = %s
#                     WHERE patient_id = %s
#                 """, [full_name, date_of_birth, age, gender, address, phone_number, email, dependent_name, dependent_contact, insurance, patient_id])
                
#                 connection.commit()
#                 messages.success(request, 'Patient details updated successfully!')
#                 return redirect('patient_list')  # Redirect to patient list after successful update

#         except Exception as e:
#             connection.rollback()
#             messages.error(request, f"Error updating patient details: {str(e)}")

#     context = {
#         'patient': patient,
#         'username': username,
#         'user_id': user_id,
#     }

#     return render(request, 'dashboard/almoner/edit_patient.html', context)

# ======================


def edit_patient(request, patient_id):
    # Check if the user is logged in
    if 'user_id' not in request.session:
        return redirect('login')

    # Get session details
    username = request.session.get('username')
    user_id = request.session.get('user_id')

    try:
        with connection.cursor() as cursor:
            # Handle form submission
            if request.method == 'POST':
                full_name = request.POST.get('full_name')
                date_of_birth = request.POST.get('date_of_birth')
                age = int(request.POST.get('age', 0))
                gender = request.POST.get('gender')
                address = request.POST.get('address')
                phone_number = request.POST.get('phone_number', '')
                email = request.POST.get('email', '')
                dependent_name = request.POST.get('dependent_name')
                dependent_contact = request.POST.get('dependent_contact')
                insurance = request.POST.get('insurance')

                # Update patient information
                cursor.execute("""
                    UPDATE patients 
                    SET full_name = %s, date_of_birth = %s, age = %s, gender = %s, address = %s, 
                        phone_number = %s, email = %s, dependent_name = %s, dependent_contact = %s, insurance = %s
                    WHERE patient_id = %s
                """, [full_name, date_of_birth, age, gender, address, phone_number, email, dependent_name, dependent_contact, insurance, patient_id])

                connection.commit()
                messages.success(request, 'Patient details updated successfully!')
                return redirect('patientmanagement')  # Redirect after successful update

            # Get patient data for the form
            cursor.execute("SELECT * FROM patients WHERE patient_id = %s", [patient_id])
            patient_data = cursor.fetchone()

            if not patient_data:
                messages.error(request, 'Patient not found.')
                return redirect('patientmanagement')

            # Map patient data to dictionary
            patient = {
                'patient_id': patient_data[0],
                'full_name': patient_data[1],
                'date_of_birth': patient_data[2],
                'age': patient_data[3],
                'gender': patient_data[4],
                'address': patient_data[5],
                'phone_number': patient_data[6],
                'email': patient_data[7],
                'dependent_name': patient_data[8],
                'dependent_contact': patient_data[9],
                'insurance': patient_data[10],
            }

            # Render the edit patient form with patient details
            context = {
                'patient': patient,
                'username': username,
                'user_id': user_id
            }

            return render(request, 'dashboard/almoner/edit_patient.html', context)

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('patientmanagement')



#####################################      edit visits              ######################################################
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection

def edit_visit(request, visit_id):
    # Check if the user is logged in
    if 'user_id' not in request.session:
        return redirect('login')

    # Get session details
    username = request.session.get('username')
    user_id = request.session.get('user_id')

    try:
        with connection.cursor() as cursor:
            # Handle form submission
            if request.method == 'POST':
                visit_date = request.POST.get('visit_date')
                reason_visit = request.POST.get('reason_visit')

                # Update patient visit information
                cursor.execute("""
                    UPDATE visit 
                    SET visit_date = %s, reason_for_visit = %s
                    WHERE visit_id = %s
                """, [visit_date, reason_visit, visit_id])

                messages.success(request, 'Patient visit updated successfully!')
                return redirect('visitmanagement')  # Redirect after successful update

            # Get patient visit data for the form
            cursor.execute("SELECT visit_id, patient_id, visit_date, reason_for_visit FROM visit WHERE visit_id = %s", [visit_id])
            visit_data = cursor.fetchone()

            if not visit_data:
                messages.error(request, 'Patient visit not found.')
                return redirect('visitmanagement')

            # Map visit data to dictionary
            visit = {
                'visit_id': visit_data[0],
                'patient_id': visit_data[1],
                'visit_date': visit_data[2].strftime('%Y-%m-%d'),  # Format date for input field
                'reason_visit': visit_data[3],
            }

            # Render the edit patient visit form with visit details
            context = {
                'visit': visit,
                'username': username,
                'user_id': user_id,
            }

            return render(request, 'dashboard/almoner/edit_visit.html', context)

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('visitmanagement')






def edit_appointment(request, appointment_id):
    # Check if the user is logged in
    if 'user_id' not in request.session:
        return redirect('login')

    # Get session details
    username = request.session.get('username')
    user_id = request.session.get('user_id')

    try:
        with connection.cursor() as cursor:
            # Handle form submission
            if request.method == 'POST':
                appointment_date = request.POST.get('appointment_date')
                reason_appointment = request.POST.get('reason_appointment')

                # Update patient appointment information
                cursor.execute("""
                    UPDATE appointment 
                    SET appointment_date = %s, reason_for_appointment = %s
                    WHERE appointment_id = %s
                """, [appointment_date, reason_appointment, appointment_id])

                messages.success(request, 'Patient appointment updated successfully!')
                return redirect('appointmentmanagement')  # Redirect after successful update

            # Get patient visit data for the form
            cursor.execute("SELECT appointment_id, patient_id, appointment_date, reason_for_appointment FROM appointment WHERE appointment_id = %s", [appointment_id])
            appointment_data = cursor.fetchone()

            if not appointment_data:
                messages.error(request, 'Patient appointment not found.')
                return redirect('appointmentmanagement')

            # Map visit data to dictionary
            appointment = {
                'appointment_id': appointment_data[0],
                'patient_id': appointment_data[1],
                'visit_date': appointment_data[2].strftime('%Y-%m-%d'),  # Format date for input field
                'reason_appointment': appointment_data[3],
            }

            # Render the edit patient visit form with visit details
            context = {
                'appointment': appointment,
                'username': username,
                'user_id': user_id,
            }

            return render(request, 'dashboard/almoner/edit_appointment.html', context)

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('appointmentmanagement')



##############################################################################################################################################################


                                                              


##############################################################################################################################################################


def search_authorized_patients(request):
    search_term = request.GET.get('term', '')
    
    if not search_term:
        return JsonResponse([], safe=False)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT p.patient_id, p.full_name
                FROM patients p
                INNER JOIN AuthorizedPatientForConsultation apc 
                ON p.patient_id = apc.patient_id
                WHERE (p.patient_id LIKE %s OR LOWER(p.full_name) LIKE %s)
                AND apc.status = 'incomplete'
                ORDER BY p.full_name
                LIMIT 10
            """, [f'%{search_term}%', f'%{search_term.lower()}%'])
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'patient_id': row[0],
                    'full_name': row[1]
                })
                
            return JsonResponse(results, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)