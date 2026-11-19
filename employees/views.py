
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.views.decorators.http import require_POST
from rest_framework import viewsets
from .models import Employee, Department
from .serializers import EmployeeSerializer, DepartmentSerializer

from .models import Department, Employee
from .forms import EmployeeForm, DepartmentForm


# Check HR Manager or Admin
def is_hr(user):
    return (
        user.is_authenticated and
        (
            user.is_superuser or
            user.groups.filter(name='HR Manager').exists()
        )
    )


# HR permission decorator
hr_required = user_passes_test(
    is_hr,
    login_url='/login/'
)


# Dashboard
@login_required
def dashboard(request):

    context = {
        'total_employees': Employee.objects.count(),

        'active_employees': Employee.objects.filter(
            status='Active'
        ).count(),

        'inactive_employees': Employee.objects.filter(
            status='Inactive'
        ).count(),

        'total_departments': Department.objects.count(),

        'department_counts': Department.objects.annotate(
            total=Count('employees')
        ),

        'recent_employees': Employee.objects.select_related(
            'department'
        ).order_by('-joining_date')[:5],
    }

    return render(request, 'employees/dashboard.html', context)


# Employee List
@login_required
def employee_list(request):

    employees = Employee.objects.select_related('department')

    search = request.GET.get('search', '').strip()
    department = request.GET.get('department', '')
    status = request.GET.get('status', '')
    sort = request.GET.get('sort', 'name')

    # Search employees
    if search:
        query = (
            Q(name__icontains=search) |
            Q(email__icontains=search)
        )

        if search.isdigit():
            query |= Q(pk=int(search))

        employees = employees.filter(query)

    # Department filter
    if department.isdigit():
        employees = employees.filter(
            department_id=int(department)
        )

    # Status filter
    if status in ['Active', 'Inactive']:
        employees = employees.filter(status=status)

    # Sorting
    sort_options = {
        'name': 'name',
        '-name': '-name',
        'salary': 'salary',
        '-salary': '-salary',
        'joining_date': 'joining_date',
        '-joining_date': '-joining_date',
    }

    employees = employees.order_by(
        sort_options.get(sort, 'name')
    )

    # Pagination
    paginator = Paginator(employees, 10)

    page_obj = paginator.get_page(
        request.GET.get('page')
    )

    context = {
        'employees': page_obj,
        'page_obj': page_obj,
        'departments': Department.objects.all(),
        'search': search,
        'selected_department': department,
        'selected_status': status,
        'selected_sort': sort,
    }

    return render(
        request,
        'employees/employee_list.html',
        context
    )


# Employee Details
@login_required
def employee_detail(request, pk):

    employee = get_object_or_404(Employee, pk=pk)

    return render(
        request,
        'employees/employee_detail.html',
        {'employee': employee}
    )

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related('department')
    serializer_class = EmployeeSerializer

# Add Employee
@hr_required
def employee_add(request):

    form = EmployeeForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():

        form.save()

        messages.success(
            request,
            'Employee added successfully!'
        )

        return redirect('employee_list')

    return render(
        request,
        'employees/employee_form.html',
        {
            'form': form,
            'title': 'Add Employee'
        }
    )


# Edit Employee
@hr_required
def employee_edit(request, pk):

    employee = get_object_or_404(Employee, pk=pk)

    form = EmployeeForm(
        request.POST or None,
        instance=employee
    )

    if request.method == 'POST' and form.is_valid():

        form.save()

        messages.success(
            request,
            'Employee updated successfully!'
        )

        return redirect('employee_list')

    return render(
        request,
        'employees/employee_form.html',
        {
            'form': form,
            'title': 'Update Employee'
        }
    )


# Delete Employee
@hr_required
def employee_delete(request, pk):

    employee = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':

        employee.delete()

        messages.success(
            request,
            'Employee deleted successfully!'
        )

        return redirect('employee_list')

    return render(
        request,
        'employees/employee_confirm_delete.html',
        {'employee': employee}
    )


# Activate / Deactivate Employee
@hr_required
@require_POST
def employee_toggle_status(request, pk):

    employee = get_object_or_404(Employee, pk=pk)

    if employee.status == 'Active':
        employee.status = 'Inactive'
    else:
        employee.status = 'Active'

    employee.save()

    messages.success(
        request,
        'Employee status updated successfully!'
    )

    return redirect('employee_list')


# Department List
@login_required
def department_list(request):

    departments = Department.objects.annotate(
        total=Count('employees')
    )

    return render(
        request,
        'employees/department_list.html',
        {'departments': departments}
    )


# Department Details
@login_required
def department_detail(request, pk):

    department = get_object_or_404(Department, pk=pk)

    employees = department.employees.all()

    return render(
        request,
        'employees/department_detail.html',
        {
            'department': department,
            'employees': employees
        }
    )


# Add Department
@hr_required
def department_add(request):

    form = DepartmentForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():

        form.save()

        messages.success(
            request,
            'Department added successfully!'
        )

        return redirect('department_list')

    return render(
        request,
        'employees/department_form.html',
        {
            'form': form,
            'title': 'Add Department'
        }
    )
class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer



# Edit Department
@hr_required
def department_edit(request, pk):

    department = get_object_or_404(Department, pk=pk)

    form = DepartmentForm(
        request.POST or None,
        instance=department
    )

    if request.method == 'POST' and form.is_valid():

        form.save()

        messages.success(
            request,
            'Department updated successfully!'
        )

        return redirect('department_list')

    return render(
        request,
        'employees/department_form.html',
        {
            'form': form,
            'title': 'Edit Department'
        }
    )


# Delete Department
@hr_required
def department_delete(request, pk):

    department = get_object_or_404(Department, pk=pk)

    if request.method == 'POST':

        try:
            department.delete()

            messages.success(
                request,
                'Department deleted successfully!'
            )

        except ProtectedError:
            messages.error(
                request,
                'Cannot delete department because employees are assigned.'
            )

        return redirect('department_list')

    return render(
        request,
        'employees/department_confirm_delete.html',
        {'department': department}
    )
