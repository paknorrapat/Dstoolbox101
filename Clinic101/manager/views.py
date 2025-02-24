from django.shortcuts import render,get_object_or_404,redirect
from base.models import *
from django.core.paginator import Paginator
from django.db.models import Q,Count,Sum
from datetime import datetime
from django.db.models.functions import TruncMonth,ExtractDay, ExtractHour, ExtractWeekDay
from django.utils.timezone import now,localtime
from django.contrib.auth.decorators import user_passes_test,login_required

def is_manager(user):
    return user.is_authenticated and user.is_manager

def calculate_age(birth_date):
    today = datetime.now()
    return today.year - birth_date.year - ((today.month,today.day)<(birth_date.month, birth_date.day))



@user_passes_test(is_manager, login_url='login')
def dashboard(request):
    # กำหนดช่วงเวลา
    today_date = localtime(now()).date()  # ดึงวันที่วันนี้

    # คำนวณรายได้วันนี้
    total_income_today = TreatmentHistory.objects.filter(
        appointment__date=today_date  # ใช้ฟิลด์ date ในโมเดล Appointment
    ).aggregate(Sum('cost'))['cost__sum'] or 0

    # ดึงเดือนและปีปัจจุบัน
    current_date = now()
    current_month = current_date.month
    current_year = current_date.year

    # กรองรายได้เฉพาะเดือนและปีปัจจุบัน
    total_income_month = TreatmentHistory.objects.filter(
       appointment__date__year=current_year,
       appointment__date__month=current_month,
    ).aggregate(Sum('cost'))['cost__sum'] or 0

    # คำนวณรายได้ทั้งหมด
    total_income_all = TreatmentHistory.objects.filter(appointment__date__year=current_year).aggregate(Sum('cost'))['cost__sum'] or 0

    # รับค่าปี, เดือน, และวันจาก GET parameter
    selected_year = request.GET.get('year', None)
    selected_month = request.GET.get('month', None)
    selected_day = request.GET.get('day', None)

    # ตรวจสอบปี (ค่าเริ่มต้นเป็นปีปัจจุบัน)
    if not selected_year or not selected_year.isdigit():
        selected_year = now().year
    else:
        selected_year = int(selected_year)

    # ตรวจสอบเดือน (ค่าเริ่มต้นเป็น None เพื่อหมายถึงทั้งปี)
    if selected_month and selected_month.isdigit():
        selected_month = int(selected_month)
    else:
        selected_month = None

    # ตรวจสอบวัน (ค่าเริ่มต้นเป็น None เพื่อหมายถึงทั้งเดือน)
    if selected_day and selected_day.isdigit():
        selected_day = int(selected_day)
    else:
        selected_day = None

  
    # สร้างตัวกรองสำหรับ TreatmentHistory
    date_filter = {'appointment__date__year': selected_year}
    if selected_month:
        date_filter['appointment__date__month'] = selected_month
    if selected_day:
        date_filter['appointment__date__day'] = selected_day

    # รายได้รวมตามเดือน
    revenue_by_month = (
        TreatmentHistory.objects.filter(**date_filter)
        .annotate(month=TruncMonth('appointment__date'))
        .values('month')
        .annotate(total_revenue=Sum('cost'))
        .order_by('month')
    )
    # รายได้รวมแยกตามประเภทการรักษา
    revenue_by_treatment = (
        TreatmentHistory.objects.filter(**date_filter)
        .values('appointment__treatment__treatmentName')
        .annotate(total_revenue=Sum('cost'))
        .order_by('-total_revenue')
    )

    # การนับจำนวนการนัดหมายตามประเภทการรักษา
    treatment_popularity = (
        Appointment.objects.filter(status="สำเร็จ",date__year = selected_year)
        .values('treatment__treatmentName')
        .annotate(total_appointments=Count('id'))
        .order_by('-total_appointments')  # เรียงตามจำนวนการนัดหมายมากไปน้อย
    )

     # สร้างตัวกรองสำหรับ Appointment
    apt_filter = {'date__year': selected_year}
    if selected_month:
        apt_filter['date__month'] = selected_month
    if selected_day:
        apt_filter['date__day'] = selected_day

    # กรองการนัดหมายตามปี, เดือน, และวัน
    appointments = Appointment.objects.filter(**apt_filter,
                                              date__isnull=False,      # กรองเฉพาะรายการที่มีวัน
                                              time_slot__isnull=False  # กรองเฉพาะรายการที่มีเวลา
                                              )
    appointments_by_status = appointments.values('status').annotate(total=Count('id'))
    appointments_by_month = appointments.annotate(month=TruncMonth('date')).values('month').annotate(total=Count('id')).order_by('month')

     # แมปตัวเลขเดือนเป็นชื่อเดือนภาษาไทย
    month_names = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
                   "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    for month in revenue_by_month:
        month_number = month['month'].month
        month['month_name'] = month_names[month_number - 1]

    for month in appointments_by_month:
        month_number = month['month'].month
        month['month_name'] = month_names[month_number - 1]

    # สร้างตัวเลือกปี, เดือน, และวัน
    years = range(2022, now().year + 1)
    months = [
        (1, "มกราคม"), (2, "กุมภาพันธ์"), (3, "มีนาคม"), (4, "เมษายน"),
        (5, "พฤษภาคม"), (6, "มิถุนายน"), (7, "กรกฎาคม"), (8, "สิงหาคม"),
        (9, "กันยายน"), (10, "ตุลาคม"), (11, "พฤศจิกายน"), (12, "ธันวาคม")
    ]
    days = range(1, 32)
    return render(request,'manager/second_dashboard.html',{'revenue_by_month': revenue_by_month,
                                                           'revenue_by_treatment':revenue_by_treatment,
                                                           'treatment_popularity': treatment_popularity,
                                                           'appointments_by_month': appointments_by_month,
                                                           'appointments_by_status': appointments_by_status,
                                                           'total_income_today': total_income_today,
                                                           'total_income_month': total_income_month,
                                                           'total_income_all': total_income_all,
                                                            'years': years,
                                                            'months': months,
                                                            'days': days,
                                                            'selected_year': selected_year,
                                                            'selected_month': selected_month,
                                                            'selected_day': selected_day,                                                          
                                                          })

@user_passes_test(is_manager, login_url='login')
def user_list(request):
    search = request.GET.get("search","")
    if search:
        users = User.objects.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search),is_superuser=False,is_manager=False,is_staff=False)
    else :
        users = User.objects.filter(is_superuser=False,is_manager=False,is_staff=False)

    #paginator
    paginator = Paginator(users,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request,"manager/user_list.html",{"page_obj":page_obj})

@user_passes_test(is_manager, login_url='login')
def update_role(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        role = request.POST.get("role")
        user = get_object_or_404(User, id=user_id)
        if role == "Staff":
            user.is_staff = True
            user.save()
            return redirect('staff-list')
        else:  # Member
            user.is_staff = False
            user.save()
            return redirect('user-list')


@user_passes_test(is_manager, login_url='login')
def staff_list(request):
    users = User.objects.filter(is_staff=True,is_superuser=False)

    #paginator
    paginator = Paginator(users,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request,"manager/staff_list.html",{"page_obj":page_obj})

@user_passes_test(is_manager, login_url='login')
def delete_user(request,user_id):
    user = get_object_or_404(User,id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('user-list')
    return redirect('user-list')