from django.shortcuts import render,redirect,get_object_or_404,reverse
from base.models import *
from .forms import AppointmentForm
from django.http import JsonResponse
from datetime import datetime,date,timedelta
import json
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q,Sum,Count
from django.utils.timezone import now
from django.contrib.auth.decorators import user_passes_test,login_required
from django.http import HttpResponseForbidden

def is_member(user):
    return user.is_authenticated 
# Create your views here.
@user_passes_test(is_member, login_url='login')
def member_home(request):
    search = request.GET.get("search","")
    if search:
        dentists = Dentist.objects.filter(
        dentistName__icontains=search  # ค้นหาโดยไม่สนตัวพิมพ์ใหญ่-เล็ก
    )
    else:
        dentists = Dentist.objects.all()

    for dentist in dentists:
        # แปลง workDays เป็นชื่อวันในภาษาไทย
        dentist.workDaysThai = get_day_name(dentist.workDays)

    treatments = Treatment.objects.all()
    
    appointments = Appointment.objects.filter(user = request.user).order_by('-createdAt')

    treatment_history = TreatmentHistory.objects.all()
    
    # ฟิลเตอร์นัดหมายที่มีวันที่ตรงกับวันนี้ 
    today = timezone.now().date()
    appointment_today = Appointment.objects.filter(user = request.user,date=today).order_by('time_slot')

    count_appointment_all =appointments.count()
    count_appointment_today =appointment_today.count()
    success_or_fail_today =appointment_today.filter(Q(status="สำเร็จ") | Q(status="ไม่สำเร็จ")).count()

    # pagination
    paginator = Paginator(appointment_today,5) # แบ่งเป็นหน้า 5 รายการต่อหน้า
    appointment_page_number = request.GET.get('appointment_page')
    appointment_page_obj = paginator.get_page(appointment_page_number)

    # pagination 2
    paginator2 = Paginator(dentists,5) # แบ่งเป็นหน้า 5 รายการต่อหน้า
    user_page_number = request.GET.get('user_page')
    user_page_obj = paginator2.get_page(user_page_number)

    # pagination 3
    paginator3 = Paginator(appointments,5) # แบ่งเป็นหน้า 5 รายการต่อหน้า
    aptall_page_number = request.GET.get('aptall_page')
    aptall_page_obj = paginator3.get_page(aptall_page_number)

    return render(request,"member/member_home.html",{
        "appointment_today":appointment_today,
        'aptall_page_obj' : aptall_page_obj,
        'appointment_page_obj': appointment_page_obj,
        'user_page_obj': user_page_obj,
        'dentists':dentists,
        'treatments':treatments,
        'treatment_history':treatment_history,
        'count_appointment_today': count_appointment_today,
        "success_or_fail_today":success_or_fail_today,
        "count_appointment_all":count_appointment_all,
    })

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

@login_required(login_url='login')
def t_history(request,user_id):
    t_history = TreatmentHistory.objects.filter(appointment__user = user_id).order_by('-appointment__date')
    # ตรวจสอบว่าเป็นเจ้าของข้อมูล, staff, หรือ dentist
    if request.user.id != user_id and not request.user.is_staff and not request.user.is_dentist:
        return HttpResponseForbidden("คุณไม่มีสิทธิ์เข้าถึงประวัติการรักษานี้")
    
     # pagination
    paginator = Paginator(t_history,10) # แบ่งเป็นหน้า 10 รายการต่อหน้า
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request,"member/t_history.html",{'page_obj':page_obj})

@login_required(login_url='login')
def braces_progress(request,user_id):
    treatment_history = TreatmentHistory.objects.filter(appointment__user = user_id).order_by('-appointment__date')
    braces = treatment_history.filter(appointment__treatment__is_braces=True)

     # ตรวจสอบว่าเป็นเจ้าของข้อมูล, staff
    if request.user.id != user_id and not request.user.is_staff:
        return HttpResponseForbidden("คุณไม่มีสิทธิ์เข้าถึงสถานะการจัดฟันนี้")
    
     # pagination
    paginator = Paginator(braces,10) # แบ่งเป็นหน้า 10 รายการต่อหน้า
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # คำนวณค่าใช้จ่ายทั้งหมดสำหรับการจัดฟัน
    total_cost = treatment_history.filter(appointment__treatment__is_braces=True).aggregate(total=Sum('cost'))['total'] or 0

    # ค่าใช้จ่ายของ "เคลียร์ช่องปาก"
    clear_cost = treatment_history.filter(
        appointment__treatment__treatmentName='เคลียร์ช่องปาก'
    ).aggregate(total=Sum('cost'))['total'] or 0

    max_cost = 40000 + clear_cost # ค่าใช้จ่ายรวมทั้งหมด
    percentage_paid = min((total_cost / max_cost) * 100, 100)  # จำกัดไม่เกิน 100%

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

    
    return render(request,"member/braces_progress.html",{"treatment_history": treatment_history,
                                                         "step1_completed": step1_completed,
                                                         "step2_completed": step2_completed,
                                                         "step3_completed": step3_completed,
                                                         "step4_completed": step4_completed,
                                                         "step4_count": step4_count,
                                                         "step4_total": step4_total,
                                                         "step5_completed": step5_completed,
                                                         "total_cost":total_cost,
                                                         "braces":braces,
                                                         'page_obj':page_obj,
                                                         "percentage_paid": round(percentage_paid, 2),
                                                         "max_cost": max_cost,
                                                         })

@user_passes_test(is_member, login_url='login')
def appointment_view(request,dentist_id):
    dentist = get_object_or_404(Dentist, id=dentist_id) 
    treatments = Treatment.objects.all()
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)

            appointment.user = request.user
            appointment.dentist = dentist  # กำหนด Dentist ที่เลือก
            appointment.save()
            return redirect('member-home')
    else:
        form = AppointmentForm()
    
    return render(request,'appointment/appointment_form.html',{'form':form,'dentist':dentist,'treatments':treatments})

@login_required(login_url='login')
def get_time_slots(request):

    date_str = request.GET.get('date')
    dentist_id = request.GET.get('dentist_id')  # รับ dentist_id เพื่อกรองเวลาสำหรับทันตแพทย์เฉพาะ 

    if request.user.is_staff:
        user_id = request.GET.get('user_id')
    else:
        user_id = request.user.id  
       
    if not date_str:
        return JsonResponse({'slots':[]})
    
    selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    # ดักไม่ให้นัดหมายย้อนหลัง (วันที่ต้องไม่ก่อนวันที่ปัจจุบัน)
    today = datetime.today().date()
    if selected_date < today:
        return JsonResponse({'slots': []})  # หากวันที่ที่เลือกย้อนหลัง ให้คืนค่าช่องว่าง

    dentist = Dentist.objects.filter(id=dentist_id).first()
    if not dentist:
        return JsonResponse({'slots': []})
    
    # ตรวจสอบวันปิดทำการ
    if ClosedDay.objects.filter(dentist=dentist, date=selected_date).exists():
        return JsonResponse({'slots': []})  # หากวันนั้นเป็นวันปิดทำการ ให้คืนค่าช่องว่าง
    
    # ตรวจสอบว่าวันที่เลือกอยู่ในวันทำงานของทันตแพทย์หรือไม่
    selected_weekday = str(selected_date.isoweekday())  # แปลงเป็นตัวเลข (1=จันทร์, ..., 7=อาทิตย์)
    work_days = dentist.workDays.split(',')  # แปลง workDays เป็น list
    if selected_weekday not in work_days:
        return JsonResponse({'slots': []})  # หากวันไม่อยู่ในวันทำงาน ให้คืนค่าช่องว่าง


    if Appointment.objects.filter(date=selected_date,user=user_id).exists():
        return JsonResponse({'slots':[]})
    
    # ช่วงเวลาทำงานของทันตแพทย์
    start_time = dentist.startTime  # เวลาเริ่มทำงาน
    end_time = dentist.endTime      # เวลาสิ้นสุดการทำงาน
    
     # กำหนด time slots (เช่น ทุก 1 ชั่วโมง)
    time_slots = []
    current_time = datetime.combine(selected_date, start_time)
    while current_time.time() < end_time:
        time_slots.append(current_time.time())
        current_time += timedelta(minutes=60)  # เพิ่มทีละ 60 นาที

    # ตรวจสอบ slot ที่ว่าง
    booked_appointments = Appointment.objects.filter(date=selected_date,dentist_id = dentist_id).values_list('time_slot',flat=True)

    available_slots = [slot.strftime('%H:%M') for slot in time_slots if slot not in booked_appointments]

    return JsonResponse({'slots': available_slots})

@login_required(login_url='login')
def calendar_view(request):
    dentists = Dentist.objects.all()

    #ดึงข้อมูลการนัดหมายทั้งหมด และคำนวณจำนวนคิวที่ถูกจองในแต่ละวัน
    appointments_per_day = Appointment.objects.values('date','dentist_id').annotate(total_appointments=Count('id'))

    #เก็บจำนวนคิวที่เหลือในแต่ละวัน
    available_slots = {}

    #คำนวณจำนวนคิวที่รับได้จากเวลาเริ่มต้นและเวลาสิ้นสุดของทันตแพทย์
    for dentist in dentists:
        start_time = dentist.startTime
        end_time = dentist.endTime
        slot_duration = 60

        #คำนวณจำนวนคิวที่รับได้ต่อวัน
        total_slots = (datetime.combine(datetime.today(),end_time) - datetime.combine(datetime.today(),start_time)).seconds // (slot_duration * 60)

        # ดึงวันทำงานจาก `dentist.workDays`
        work_days = set(map(int, dentist.workDays.split(',')))  # แปลงเป็น `set(int)` [1=จันทร์, ..., 7=อาทิตย์]

        # สร้างวันที่ทันตแพทย์ควรทำงานตาม `workDays`
        today = datetime.today().date()
        days_ahead = 60  # แสดงล่วงหน้า 60 วัน
        working_dates = set()

        for i in range(days_ahead):
            potential_date = today + timedelta(days=i)
            if potential_date.isoweekday() in work_days:  # ตรวจสอบว่าวันนั้นอยู่ใน workDays หรือไม่
                working_dates.add(potential_date)

        # ลบวันปิดทำการออก
        closed_dates = set(ClosedDay.objects.filter(dentist=dentist).values_list('date', flat=True))
        working_dates -= closed_dates  # เอาวันที่ปิดทำการออกจากวันทำงาน

        #ตรวจสอบจำนวนคิวที่ถูกจองแล้ว
        for date in working_dates:
            booked_appointments = 0
            for apt in appointments_per_day:
                if apt['dentist_id'] == dentist.id and apt['date'] == date:
                    booked_appointments = apt['total_appointments']
                    break  # ออกจาก loop ทันทีที่เจอค่า
            
            remaining_slots = booked_appointments # ปรับให้คิวเหลือเริ่มจาก 0 และเพิ่มขึ้นเรื่อยๆ

            available_slots[(date, dentist.id)] = {
                'remaining': min(remaining_slots, total_slots),  # ป้องกันค่ามากกว่าที่ควร
                'total': total_slots
            }
                

    events = []

    for (date,dentist_id), slot_data in available_slots.items():
        dentist = Dentist.objects.get(id=dentist_id)
        events.append({
            'title': f'{dentist.dentistName}:{slot_data["remaining"]}/{slot_data["total"]} คิว',
            'start': date,
            'allDay':True,
            'color': 'gray' if slot_data["remaining"] == slot_data["total"]  else 'green',
        })
   
    # ดึงข้อมูลวันปิดทำการจากโมเดล ClosedDay
    closed_days = ClosedDay.objects.all().values(
                                                    'date',
                                                    'dentist__dentistName', 
                
                                                )

    # เพิ่ม closed days ใน events
    for closed_day in closed_days:
        events.append({
            'title': f'Closed : {closed_day["dentist__dentistName"]} ',
            'start': closed_day['date'].isoformat(),  # แปลงวันที่เป็น ISO string
            'allDay': True,                           # แสดงเป็น All Day
            'color': 'red',                           # ใช้สีแดงเพื่อแยกความแตกต่าง
        })
  
    context = {
        'events': json.dumps(events,default=str),  # แปลง events เป็น JSON string
        'dentists': dentists
 
    }
  
    return render(request, 'appointment/calendar.html', context)

@user_passes_test(is_member, login_url='login')
def select_appointment_date(request, appointment_id):
    default_redirect = reverse('appointment-all')
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)

    if request.method == 'POST':
        selected_date = request.POST.get('date')
        selected_time = request.POST.get('time_slot')

        # บันทึกวันและเวลาที่เลือก
        appointment.date = selected_date
        appointment.time_slot = selected_time
        appointment.status = 'รอดำเนินการ'  
        appointment.save()

        return redirect('appointment-all')  

   
    return render(request, 'member/select_appointment_date.html', {
        'appointment': appointment,
        'default_redirect': default_redirect,
    })

@user_passes_test(is_member, login_url='login')
def delete_appointment_member(request,id):
    appointment = get_object_or_404(Appointment,id=id)
    if request.method == 'POST':
        appointment.delete()
        return redirect('appointment-all')
    return redirect('appointment-all')

@user_passes_test(is_member, login_url='login')
def edit_appointment_member(request,id):
    appointment = get_object_or_404(Appointment,id = id)
    dentists = Dentist.objects.all() 
    treatments = Treatment.objects.all()
    if request.method == 'POST':
        form = AppointmentForm(request.POST,instance=appointment)
        if form.is_valid():
            form.save()
            return redirect('appointment-all')
        else:
            form = AppointmentForm(instance=appointment)
    return render(request,'member/edit_appointment_member.html',{'appointment':appointment,'dentists':dentists,
        'treatments':treatments,})

@user_passes_test(is_member, login_url='login')
def appointment_all(request):
    dentists = Dentist.objects.all() 
    treatments = Treatment.objects.all()
    appointments = Appointment.objects.filter(user=request.user).order_by('-date')

    today = now().date()

    #รับค่า filter จาก dropdown
    selected_day = request.GET.get('day')
    selected_month = request.GET.get('month')
    selected_year = request.GET.get('year')
    selected_status = request.GET.get('status')  # รับค่าของ status
    # กรองข้อมูล
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
    # pagination
    paginator = Paginator(appointments,10) # แบ่งเป็นหน้า 10 รายการต่อหน้า
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request,"member/appointment_all.html",{
                                                         "appointments":appointments,
                                                         "page_obj":page_obj,                                       
                                                         'dentists':dentists,
                                                         'treatments':treatments,
                                                         'today': today,
                                                         "days": days,
                                                         "months": months,
                                                         "years": years,
                                                         "statuses":statuses,                                                 
                                                         "selected_day": selected_day,
                                                         "selected_month": selected_month,
                                                         "selected_year": selected_year,
                                                         "selected_status": selected_status,
                                                         "query_params": query_params.urlencode(),  # ส่ง Query Parameters ที่จัดการแล้วไปยัง Template
                                                        
                                                         })
