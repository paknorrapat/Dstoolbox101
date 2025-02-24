from django.shortcuts import render,redirect,get_object_or_404,reverse
from django.utils import timezone
from django.core.paginator import Paginator
from .forms import *
from base.models import *
from django.http import JsonResponse,HttpResponseRedirect
from django.db.models import Q
from django.utils.timezone import now
from django.contrib.auth.decorators import user_passes_test,login_required
from datetime import datetime
from django.contrib import messages

def is_staff(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_staff, login_url='login')
def staff_home(request):
    search = request.GET.get("search","")
    if search:
        users = User.objects.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search),is_manager=False,is_staff=False)
    else :
        users = User.objects.filter(is_manager=False,is_staff=False)
    
    dentists = Dentist.objects.all() 
    treatments = Treatment.objects.all()
    
    appointments = Appointment.objects.all()

    treatment_history = TreatmentHistory.objects.all()

    # ฟิลเตอร์นัดหมายที่มีวันที่ตรงกับวันนี้ 
    today = timezone.now().date()
    appointment_today = Appointment.objects.filter(date=today).order_by('time_slot')

    count_appointment_all =appointments.count()
    count_appointment_today =appointment_today.count()
    success_or_fail_today =appointment_today.filter(Q(status="สำเร็จ") | Q(status="ไม่สำเร็จ")).count()

    # pagination
    paginator = Paginator(appointment_today,6) # แบ่งเป็นหน้า 6 รายการต่อหน้า
    appointment_page_number = request.GET.get('appointment_page')
    appointment_page_obj = paginator.get_page(appointment_page_number)

    # pagination 2 add+
    paginator2 = Paginator(users,5) # แบ่งเป็นหน้า 5 รายการต่อหน้า
    user_page_number = request.GET.get('user_page')
    user_page_obj = paginator2.get_page(user_page_number)

    # pagination 3
    paginator3 = Paginator(appointments,5) # แบ่งเป็นหน้า 5 รายการต่อหน้า
    aptall_page_number = request.GET.get('aptall_page')
    aptall_page_obj = paginator3.get_page(aptall_page_number)

    
    return render(request,"staff/staff_home.html",{
        "appointment_today":appointment_today,
        'aptall_page_obj' : aptall_page_obj,
        'appointment_page_obj': appointment_page_obj,
        'user_page_obj': user_page_obj,
        'dentists':dentists,
        'treatments':treatments,
        'users':users,
        'treatment_history':treatment_history,
        'count_appointment_today': count_appointment_today,
        "success_or_fail_today":success_or_fail_today,
        "count_appointment_all":count_appointment_all
        })

@user_passes_test(is_staff, login_url='login')
def appointment_list(request):
    today = now().date()
    dentists = Dentist.objects.all() 
    treatments = Treatment.objects.all()
    appointments = Appointment.objects.all().order_by('-date')
    
    #รับค่า filter จาก dropdown
    selected_day = request.GET.get('day')
    selected_month = request.GET.get('month')
    selected_year = request.GET.get('year')
    selected_status = request.GET.get('status')  # รับค่าของ status

    search = request.GET.get("search","")
    # กรองข้อมูล
    if search:
        appointments = appointments.filter(Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search))
    if selected_day:
        appointments = appointments.filter(date__day=selected_day)
    if selected_month:
        appointments = appointments.filter(date__month=selected_month)
    if selected_year:
        appointments = appointments.filter(date__year=selected_year)
    if selected_status:  # กรองตามสถานะ
        appointments = appointments.filter(status=selected_status) 

    # จัดการ Query Parameters (ลบ key 'page')
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    # pagination
    paginator = Paginator(appointments,10) # แบ่งเป็นหน้า 10 รายการต่อหน้า
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    #ข้อมูล dropdown
    days = list(range(1,32))
    # ข้อมูลเดือน (mapping)
    months = [
    (1, "มกราคม"), (2, "กุมภาพันธ์"), (3, "มีนาคม"), (4, "เมษายน"),
    (5, "พฤษภาคม"), (6, "มิถุนายน"), (7, "กรกฎาคม"), (8, "สิงหาคม"),
    (9, "กันยายน"), (10, "ตุลาคม"), (11, "พฤศจิกายน"), (12, "ธันวาคม")
    ]
    years =range(2021,datetime.now().year + 1)

    statuses = [
        ('รอดำเนินการ', 'รอดำเนินการ'),  
        ('สำเร็จ', 'สำเร็จ'),         
        ('ไม่สำเร็จ', 'ไม่สำเร็จ'),
    ]
    return render(request,"staff/appointment_list.html",{
                                                         "appointments":appointments,
                                                         "page_obj":page_obj,                                       
                                                         'dentists':dentists,
                                                         'treatments':treatments,
                                                         'today': today,
                                                         "days": days,
                                                         "months": months,
                                                         "years": years,
                                                         "statuses": statuses, 
                                                         "selected_day": selected_day,
                                                         "selected_month": selected_month,
                                                         "selected_year": selected_year,
                                                         "selected_status": selected_status,
                                                         "query_params": query_params.urlencode()  # ส่ง Query Parameters ที่จัดการแล้วไปยัง Template
                                                         })
@user_passes_test(is_staff, login_url='login')
def delete_appointment(request,id):
    appointment = get_object_or_404(Appointment,id=id)
    if request.method == 'POST':
        appointment.delete()
        return redirect('appointment-list')
    return redirect('appointment-list')

@user_passes_test(is_staff, login_url='login')
def add_appointment(request,user_id):
     # ตรวจสอบว่า user_id ถูกต้องหรือไม่
    user = get_object_or_404(User, id=user_id)
    
    dentists = Dentist.objects.all() 
    treatments = Treatment.objects.all()

    treatment_history = TreatmentHistory.objects.filter(appointment__user = user_id)

    dentist_braces = TreatmentHistory.objects.filter(appointment__user = user_id,appointment__treatment__treatmentName='ปรึกษาวางแผนจัดฟัน', status=True
    )
   
    # ดึงชื่อทันตแพทย์ในรูปแบบที่อ่านง่าย
    dentist_name_list = [
        f"{dentist['appointment__dentist__dentistName']}"
        for dentist in dentist_braces.values('appointment__dentist__dentistName')
    ]

    # ตรวจสอบสถานะของ "ปรึกษาวางแผนจัดฟัน"
    step1_completed = treatment_history.filter(
        appointment__treatment__treatmentName='ปรึกษาวางแผนจัดฟัน', status=True
    ).exists()

    # ตรวจสอบสถานะของ "เคลียร์ช่องปาก"
    step2_completed = treatment_history.filter(
        appointment__treatment__treatmentName='เคลียร์ช่องปาก', status=True
    ).exists()

    # ตรวจสอบสถานะของ "พิมพ์ปากและเอกซเรย์"
    step3_completed = treatment_history.filter(
        appointment__treatment__treatmentName='พิมพ์ปากและเอกซเรย์', status=True
    ).exists()

    # ตรวจสอบสถานะของ "ติดเครื่องมือ"
    step4_total = 30  # จำนวนครั้งที่ต้องการ
    step4_count = treatment_history.filter(
        appointment__treatment__treatmentName='ติดเครื่องมือ', status=True
    ).count()
    step4_completed = step4_count >= step4_total

    # ตรวจสอบสถานะของ "ถอดเครื่องมือ"
    step5_completed = treatment_history.filter(
        appointment__treatment__treatmentName='ถอดเครื่องมือ', status=True
    ).exists()

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.user = user
            appointment.save()

             # ตรวจสอบว่าการรักษาคือ "ติดเครื่องมือ"
            if appointment.treatment.treatmentName == "ติดเครื่องมือ":
                # กำหนดรายละเอียดให้กับ appointment แรก
                appointment.detail = "ครั้งที่ 1"
                appointment.status = "รอดำเนินการ"
                appointment.save()
                # สร้างนัดหมาย 29 รายการ
                appointments = []
                for i in range(2, 31):  # ตั้งแต่ 2 ถึง 30
                    appointments.append(Appointment(
                        user=user,
                        treatment=appointment.treatment,
                        dentist=appointment.dentist,
                        date=None,  # ยังไม่ได้เลือกวัน
                        time_slot=None,  # ยังไม่ได้เลือกเวลา
                        status='รอดำเนินการ',  # สถานะเริ่มต้น
                        detail=f'ครั้งที่ {i}'  # ระบุรายละเอียดเป็น "ครั้งที่ i"
                    ))

                # บันทึกในฐานข้อมูล
                Appointment.objects.bulk_create(appointments)

            return redirect('staff-home')
    else:
        form = AppointmentForm()
    return render(request,'staff/add_appointment.html',{'user': user,
                                                        'dentists':dentists,
                                                        'treatments':treatments,
                                                        "step1_completed": step1_completed,
                                                         "step2_completed": step2_completed,
                                                         "step3_completed": step3_completed,
                                                         "step4_completed": step4_completed,
                                                         "step4_count": step4_count,
                                                         "step4_total": step4_total,
                                                         "step5_completed": step5_completed,
                                                         'dentist_names': dentist_name_list,
                                                       
                                                        })

@user_passes_test(is_staff, login_url='login')
def update_appointment(request,appointment_id):
    appointment = get_object_or_404(Appointment,id = appointment_id)
    dentists = Dentist.objects.all() 
    treatments = Treatment.objects.all()
    if request.method == 'POST':
        form = AppointmentStatus(request.POST,instance=appointment)
        if form.is_valid():
            form.save()
           
            return redirect('appointment-list')
        
    return render(request,'staff/edit_appointment.html',{'appointment':appointment,'dentists':dentists,
        'treatments':treatments,})


@user_passes_test(is_staff, login_url='login')
def dentist_manage(request): 
    users = Dentist.objects.filter(workDays__isnull=False).exclude(workDays='')
    dentists = Dentist.objects.all()
    for user in users:
        # แปลง workDays เป็นชื่อวันในภาษาไทย
        user.workDaysThai = get_day_name(user.workDays)

    # pagination
    paginator = Paginator(users, 10)  # แบ่งเป็นหน้า 10 รายการต่อหน้า
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'staff/dentist_manage.html', {'users': users, 'page_obj': page_obj,'dentists':dentists})

def get_day_name(day_numbers):
    days_map = {
        "1": "จันทร์",
        "2": "อังคาร",
        "3": "พุธ",
        "4": "พฤหัสบดี",
        "5": "ศุกร์",
        "6": "เสาร์",
        "7": "อาทิตย์"
    }
    return ", ".join([days_map.get(day, "") for day in day_numbers.split(",")]) 
   
@user_passes_test(is_staff, login_url='login')
def add_dentist(request):
    if request.method == 'POST':
        form = DentistForm(request.POST)
        if form.is_valid():
            dentist = form.save(commit=False)  # บันทึกข้อมูลก่อน แต่ไม่ commit
            work_days = request.POST.getlist('workDays')  # ใช้ getlist เพื่อรับค่าหลายค่า
            dentist.workDays = ",".join(work_days)  # เก็บค่า workDays เป็น string ที่แยกด้วยเครื่องหมายจุลภาค
            dentist.save()  # บันทึกข้อมูลทันตแพทย์
            return redirect('dentist-manage') 
        
    return redirect('dentist-manage')

@user_passes_test(is_staff, login_url='login')
def delete_dentist(request,dentist_id):
    dentist = get_object_or_404(Dentist,id=dentist_id)
    if request.method == 'POST':
        dentist.delete()
        return redirect('dentist-manage')
    return redirect('dentist-manage')

@user_passes_test(is_staff, login_url='login')
def edit_dentist(request,dentist_id):
    dentist = get_object_or_404(Dentist,id = dentist_id)
    dentist.startTime = dentist.startTime.strftime('%H:%M') if dentist.startTime else ""
    dentist.endTime = dentist.endTime.strftime('%H:%M') if dentist.endTime else ""
    if request.method == 'POST' :
        form = DentistForm(request.POST,instance=dentist)
        if form.is_valid():
             # รับค่า workDays ที่เลือกทั้งหมด
            work_days = request.POST.getlist('workDays')  # ใช้ getlist เพื่อรับค่าหลายค่า
            dentist.workDays = ",".join(work_days)  # เก็บค่า workDays เป็น string ที่แยกด้วยเครื่องหมายจุลภาค
            form.save()
            return redirect('dentist-manage')
    else:
        form = DentistForm(instance=dentist)
    return render(request,'staff/edit_dentist.html',{'dentist':dentist})

@user_passes_test(is_staff, login_url='login')
def treatment_manage(request): 
    treatments = Treatment.objects.all()
 
    
    # pagination
    paginator = Paginator(treatments,5) # แบ่งเป็นหน้า 5 รายการต่อหน้า
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    return render(request,'staff/treatment_manage.html',{'treatments':treatments,'page_obj':page_obj})

@user_passes_test(is_staff, login_url='login')
def add_treatment(request):
    if request.method =="POST" :
        form = TreatmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("treatment-manage")
    return redirect("treatment-manage")

@user_passes_test(is_staff, login_url='login')
def delete_treatment(request,treatment_id):
    treatment = get_object_or_404(Treatment,id=treatment_id)
    if request.method == 'POST':
        treatment.delete()
        return redirect('treatment-manage')
    return redirect('treatment-manage')

@user_passes_test(is_staff, login_url='login')
def edit_treatment(request,treatment_id):
    treatment = get_object_or_404(Treatment,id=treatment_id)
    if request.method == "POST" :
        form = TreatmentForm(request.POST,instance = treatment)
        if form.is_valid():
            form.save()
            return redirect("treatment-manage")
    return render(request,"staff/edit_treatment.html",{"treatment":treatment})


@user_passes_test(is_staff, login_url='login')
def member_info(request):
    search = request.GET.get("search","")
    if search:
        users = User.objects.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search),is_manager=False,is_staff=False)
    else :
        users = User.objects.filter(is_manager=False,is_staff=False)

    # pagination 2
    paginator2 = Paginator(users,10) # แบ่งเป็นหน้า 10 รายการต่อหน้า
    user_page_number = request.GET.get('user_page')
    user_page_obj = paginator2.get_page(user_page_number)

    return render(request,"staff/member_info.html",{"users":users,"user_page_obj":user_page_obj})

@user_passes_test(is_staff, login_url='login')
def close_0ff_day(request):
    if request.method == "POST":
        date = request.POST.get('date')
        dentist_id = request.POST.get('dentist_id')
        
        # ตรวจสอบข้อมูล
        if not date or not dentist_id:
            messages.error(request, "กรุณาเลือกวันที่และทันตแพทย์")
            return redirect('calendar_view')

        dentist = Dentist.objects.filter(id=dentist_id).first()
        if not dentist:
            messages.error(request, "ไม่พบทันตแพทย์ที่เลือก")
            return redirect('calendar_view')

        # ตรวจสอบว่ามีการปิดวันในวันที่เลือกแล้วหรือยัง
        if ClosedDay.objects.filter(dentist=dentist, date=date).exists():
            messages.error(request, f"ทันตแพทย์ {dentist.dentistName} ได้ปิดวันทำการในวันนี้แล้ว!")
            return redirect('calendar')

        # บันทึกวันปิดทำการ
        ClosedDay.objects.create(date=date, dentist=dentist)
        messages.success(request, f"ปิดวันทำการสำหรับ {dentist.dentistName}  สำเร็จแล้ว!")

        # ล้าง messages หลังจากแสดงผล
        storage = messages.get_messages(request)
        list(storage)  # ดึงข้อความทั้งหมดเพื่อบังคับให้ระบบล้าง
        return redirect('calendar')

@user_passes_test(is_staff, login_url='login')
def delete_closed_day(request, pk):
    # ตรวจสอบว่ามี ClosedDay อยู่หรือไม่
    closed_day = get_object_or_404(ClosedDay, pk=pk)
    if request.method == 'POST':
        closed_day.delete()  # ลบวันปิดทำการ
        return redirect('calendar')  

@user_passes_test(is_staff, login_url='login')
def closed_day_list(request):
    closed_days = ClosedDay.objects.all().order_by('-date')

    # pagination
    paginator = Paginator(closed_days,10) # แบ่งเป็นหน้า 10 รายการต่อหน้า
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request,'staff/closed_day_list.html',{'closed_days':closed_days,'page_obj':page_obj})

@user_passes_test(is_staff, login_url='login')
def update_status_appointment(request):
    if request.method == "POST":
        appointment_id = request.POST.get("appointment_id")
        status = request.POST.get("status")

        # หานัดหมายที่มี id ตรงกับ appointment_id
        appointment = get_object_or_404(Appointment, id=appointment_id)

         # อัปเดตสถานะของนัดหมาย
        if status in ['รอดำเนินการ', 'สำเร็จ', 'ไม่สำเร็จ']:  
            appointment.status = status
            appointment.save()  # บันทึกการเปลี่ยนแปลง
            return redirect('staff-home')  # เปลี่ยนเส้นทางไปยังหน้ารายการนัดหมาย
        else:
            return redirect('staff-home')  # หรือเพิ่มข้อความแสดงข้อผิดพลาด
        

@user_passes_test(is_staff, login_url='login')
def treatment_history(request):
     # ฟิลเตอร์นัดหมายที่มีวันที่ตรงกับวันนี้ 
    today = timezone.now().date()
    appointment_today = Appointment.objects.filter(date=today,status='สำเร็จ').order_by('time_slot')
    appointments = Appointment.objects.filter(status='สำเร็จ',treatmenthistory__status=True)

    t_history = Appointment.objects.filter(status='สำเร็จ').order_by('-date')

    count_th_all =appointments.count()
    count_th_today =appointment_today.count()
    success_today =appointment_today.filter(treatmenthistory__status=True).count()

    # pagination
    paginator = Paginator(appointment_today,5) # แบ่งเป็นหน้า 5 รายการต่อหน้า
    appointment_page_number = request.GET.get('appointment_page')
    appointment_page_obj = paginator.get_page(appointment_page_number)

    # pagination
    paginator = Paginator(t_history,10) # แบ่งเป็นหน้า 10 รายการต่อหน้า
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request,"staff/treatment_history.html",{'appointment_page_obj': appointment_page_obj,
                                                            'page_obj':page_obj,
                                                            'count_th_all':count_th_all,
                                                            'count_th_today':count_th_today,
                                                            'success_today':success_today,
                                                    
                                                            })
@user_passes_test(is_staff, login_url='login')
def t_history_all(request):
    treatmenthistorys = TreatmentHistory.objects.filter(status=True).order_by('-appointment__date')
    
    #รับค่า filter จาก dropdown
    selected_day = request.GET.get('day')
    selected_month = request.GET.get('month')
    selected_year = request.GET.get('year')
 
    search = request.GET.get("search","")
    # กรองข้อมูล
    if search:
        treatmenthistorys = treatmenthistorys.filter(Q(appointment__user__first_name__icontains=search) | Q(appointment__user__last_name__icontains=search))
    if selected_day:
        treatmenthistorys = treatmenthistorys.filter(appointment__date__day=selected_day)
    if selected_month:
        treatmenthistorys = treatmenthistorys.filter(appointment__date__month=selected_month)
    if selected_year:
        treatmenthistorys = treatmenthistorys.filter(appointment__date__year=selected_year)

    # จัดการ Query Parameters (ลบ key 'page')
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    # pagination
    paginator = Paginator(treatmenthistorys,10) # แบ่งเป็นหน้า 10 รายการต่อหน้า
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    #ข้อมูล dropdown
    days = list(range(1,32))
    # ข้อมูลเดือน (mapping)
    months = [
    (1, "มกราคม"), (2, "กุมภาพันธ์"), (3, "มีนาคม"), (4, "เมษายน"),
    (5, "พฤษภาคม"), (6, "มิถุนายน"), (7, "กรกฎาคม"), (8, "สิงหาคม"),
    (9, "กันยายน"), (10, "ตุลาคม"), (11, "พฤศจิกายน"), (12, "ธันวาคม")
    ]
    years =range(2021,datetime.now().year + 1)

    return render(request,"staff/t_history_all.html",{'page_obj':page_obj,
                                                        "days": days,
                                                        "months": months,
                                                        "years": years,                                                 
                                                        "selected_day": selected_day,
                                                        "selected_month": selected_month,
                                                        "selected_year": selected_year,
                                                        "query_params": query_params.urlencode()  # ส่ง Query Parameters ที่จัดการแล้วไปยัง Template
                                                        })

@user_passes_test(is_staff, login_url='login')
def add_treatment_history(request, apt_id):
    appointment = get_object_or_404(Appointment, id=apt_id)
 
    treatments = Treatment.objects.all()

    if request.method == "POST":
        form = TreatmentHistoryForm(request.POST)
        if form.is_valid():
            treatmenthistory = form.save(commit=False)
            treatmenthistory.appointment = appointment
            treatmenthistory.status = True
            treatmenthistory.save()

            return redirect("treatment-history")
        
    return render(request, 'staff/add_t_history.html', {
      
        'appointment': appointment,
        'treatments': treatments,
    })

@user_passes_test(is_staff, login_url='login')
def update_treatment_history(request,treatment_history_id):
    # ดึง TreatmentHistory ที่ต้องการอัปเดต
    treatment_history = get_object_or_404(TreatmentHistory, id=treatment_history_id)
    if request.method == "POST":
        form = TreatmentHistoryForm(request.POST,instance=treatment_history)
        if form.is_valid():
            treatmenthistory = form.save(commit=False)
            treatment_history.status = True  # ตั้งค่า status เป็น True
            treatmenthistory.save()
            return redirect("t-history-all")
    else:
        # GET request: สร้างฟอร์มพร้อมข้อมูลเดิม
        form = TreatmentHistoryForm(instance=treatment_history)
    return render(request,"staff/update_t_history.html",{'treatment_history':treatment_history})