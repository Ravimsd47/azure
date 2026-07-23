from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from datetime import datetime
from .models import Employee, Attendance
from .forms import EmployeeForm, AttendanceForm

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'employees/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login')

@login_required
def dashboard(request):
    today = timezone.localdate()
    total_employees = Employee.objects.filter(is_active=True).count()
    
    today_attendance = Attendance.objects.filter(date=today)
    present_count = today_attendance.filter(status='Present').count()
    late_count = today_attendance.filter(status='Late').count()
    absent_count = today_attendance.filter(status='Absent').count()
    leave_count = today_attendance.filter(status='Leave').count()
    
    marked_count = today_attendance.count()
    unmarked_count = max(0, total_employees - marked_count)
    
    attendance_rate = 0
    if total_employees > 0:
        attendance_rate = round(((present_count + late_count) / total_employees) * 100, 1)
        
    recent_activities = Attendance.objects.select_related('employee').all()[:6]
    recent_employees = Employee.objects.all().order_by('-id')[:5]
    
    context = {
        'today': today,
        'total_employees': total_employees,
        'present_count': present_count,
        'late_count': late_count,
        'absent_count': absent_count,
        'leave_count': leave_count,
        'unmarked_count': unmarked_count,
        'attendance_rate': attendance_rate,
        'recent_activities': recent_activities,
        'recent_employees': recent_employees,
    }
    return render(request, 'employees/dashboard.html', context)

@login_required
def employee_list(request):
    query = request.GET.get('q', '')
    employees = Employee.objects.all()
    
    if query:
        employees = employees.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(department__icontains=query) |
            Q(designation__icontains=query)
        )
        
    return render(request, 'employees/employee_list.html', {'employees': employees, 'query': query})

@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    attendances = Attendance.objects.filter(employee=employee).order_by('-date')
    
    # Handle direct attendance quick logging for this employee from details page
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            date_str = request.POST.get('date')
            try:
                date_val = datetime.strptime(date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                date_val = timezone.localdate()
                
            attendance_record, created = Attendance.objects.get_or_create(
                employee=employee,
                date=date_val,
            )
            attendance_record.status = form.cleaned_data['status']
            attendance_record.check_in = form.cleaned_data['check_in']
            attendance_record.check_out = form.cleaned_data['check_out']
            attendance_record.notes = form.cleaned_data['notes']
            attendance_record.save()
            
            messages.success(request, f"Attendance record updated for {date_val}.")
            return redirect('employee_detail', pk=pk)
    else:
        form = AttendanceForm()
        
    # Calculate stats
    total_logs = attendances.count()
    p_count = attendances.filter(status='Present').count()
    la_count = attendances.filter(status='Late').count()
    ab_count = attendances.filter(status='Absent').count()
    le_count = attendances.filter(status='Leave').count()
    
    emp_attendance_rate = 0
    if total_logs > 0:
        emp_attendance_rate = round(((p_count + la_count) / total_logs) * 100, 1)

    context = {
        'employee': employee,
        'attendances': attendances,
        'form': form,
        'today': timezone.localdate().strftime('%Y-%m-%d'),
        'stats': {
            'total': total_logs,
            'present': p_count,
            'late': la_count,
            'absent': ab_count,
            'leave': le_count,
            'rate': emp_attendance_rate,
        }
    }
    return render(request, 'employees/employee_detail.html', context)

@login_required
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f"Employee {employee.full_name} created successfully!")
            return redirect('employee_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EmployeeForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'title': 'Add Employee'})

@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f"Employee {employee.full_name} updated successfully!")
            return redirect('employee_detail', pk=pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'employees/employee_form.html', {'form': form, 'title': 'Edit Employee', 'employee': employee})

@login_required
def attendance_sheet(request):
    date_str = request.GET.get('date', '')
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = timezone.localdate()
    else:
        target_date = timezone.localdate()
        
    employees = Employee.objects.filter(is_active=True)
    existing_attendance = {a.employee_id: a for a in Attendance.objects.filter(date=target_date)}
    
    if request.method == 'POST':
        for emp in employees:
            status_key = f"status_{emp.id}"
            check_in_key = f"check_in_{emp.id}"
            check_out_key = f"check_out_{emp.id}"
            notes_key = f"notes_{emp.id}"
            
            status = request.POST.get(status_key)
            if status:  # Only save if a status is selected
                check_in_str = request.POST.get(check_in_key) or None
                check_out_str = request.POST.get(check_out_key) or None
                notes = request.POST.get(notes_key, '')
                
                check_in = None
                check_out = None
                if check_in_str:
                    try:
                        check_in = datetime.strptime(check_in_str, '%H:%M').time()
                    except ValueError:
                        pass
                if check_out_str:
                    try:
                        check_out = datetime.strptime(check_out_str, '%H:%M').time()
                    except ValueError:
                        pass
                
                record, created = Attendance.objects.get_or_create(
                    employee=emp,
                    date=target_date,
                )
                record.status = status
                record.check_in = check_in
                record.check_out = check_out
                record.notes = notes
                record.save()
                
        messages.success(request, f"Attendance for {target_date} saved successfully.")
        return redirect('dashboard')
        
    # Prepare list data
    sheet_data = []
    for emp in employees:
        att = existing_attendance.get(emp.id)
        sheet_data.append({
            'employee': emp,
            'status': att.status if att else 'Present',
            'check_in': att.check_in.strftime('%H:%M') if att and att.check_in else '',
            'check_out': att.check_out.strftime('%H:%M') if att and att.check_out else '',
            'notes': att.notes if att and att.notes else '',
        })
        
    context = {
        'date_str': target_date.strftime('%Y-%m-%d'),
        'sheet_data': sheet_data,
    }
    return render(request, 'employees/attendance_sheet.html', context)
