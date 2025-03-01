import os
import django
# ตั้งค่า Django settings ก่อน import โมเดล
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Clinic101.settings")
django.setup()

import gradio as gr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from django.utils.timezone import now, localtime
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from base.models import TreatmentHistory, Appointment, Treatment, Dentist
from matplotlib.ticker import FuncFormatter
import matplotlib.dates as mdates
from datetime import datetime
from calendar import month_name

# ตั้งการใช้ matplotlib backend สำหรับกราฟ
import matplotlib
matplotlib.use('Agg')  # ใช้ Agg Backend สำหรับการสร้างกราฟโดยไม่ใช้ Tkinter

# ตั้งค่าสีและสไตล์
THEME_COLORS = {
    'primary': '#4F6CD9',         # สีฟ้าสำหรับแถบหลัก
    'secondary': '#29B695',       # สีเขียวมิ้นท์
    'accent': '#FF7676',          # สีส้มแดงอ่อน
    'neutral': '#516173',         # สีเทาอมฟ้า
    'background': '#F8FAFC',      # สีพื้นหลัง
    'text': '#334155',            # สีข้อความ
}

# ตั้งค่า matplotlib
plt.rcParams.update({
    'font.family': 'Tahoma',
    'font.size': 10,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'axes.labelweight': 'bold',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.linestyle': '--',
    'grid.alpha': 0.7,
    'figure.facecolor': THEME_COLORS['background'],
})

# ฟังก์ชันสำหรับฟอร์แมตเงินบาท
def money_fmt(x, pos):
    return f'{int(x):,} ฿'

# ฟังก์ชันดึงข้อมูล
def fetch_dashboard_data():
    today = localtime(now()).date()
    current_month = today.month
    current_year = today.year

    # รายได้
    total_income_today = TreatmentHistory.objects.filter(appointment__date=today).aggregate(Sum('cost'))['cost__sum'] or 0
    total_income_month = TreatmentHistory.objects.filter(appointment__date__year=current_year, appointment__date__month=current_month).aggregate(Sum('cost'))['cost__sum'] or 0
    total_income_all = TreatmentHistory.objects.aggregate(Sum('cost'))['cost__sum'] or 0

    # จำนวนการนัดหมายต่อเดือน
    appointments_by_month = (
        Appointment.objects.filter(date__year=current_year)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )

    # สถานะการนัดหมาย
    appointments_by_status = (
        Appointment.objects.values('status')
        .annotate(total=Count('id'))
    )

    # รายได้ตามประเภทการรักษา
    revenue_by_treatment = (
        TreatmentHistory.objects.values('appointment__treatment__treatmentName')
        .annotate(total_revenue=Sum('cost'))
        .order_by('-total_revenue')
    )

    # ทันตแพทย์ที่มีการนัดหมายมากที่สุด
    top_dentists = (
        Appointment.objects.values('dentist__dentistName')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    # รายได้รายเดือน
    monthly_revenue = (
        TreatmentHistory.objects.filter(appointment__date__year=current_year)
        .annotate(month=TruncMonth('appointment__date'))
        .values('month')
        .annotate(total=Sum('cost'))
        .order_by('month')
    )

    return {
        "total_income_today": total_income_today,
        "total_income_month": total_income_month,
        "total_income_all": total_income_all,
        "appointments_by_month": list(appointments_by_month),
        "appointments_by_status": list(appointments_by_status),
        "revenue_by_treatment": list(revenue_by_treatment),
        "top_dentists": list(top_dentists),
        "monthly_revenue": list(monthly_revenue),
    }

# ฟังก์ชันสร้างกราฟ
def plot_monthly_revenue(data):
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(THEME_COLORS['background'])

    if not data:
        ax.text(0.5, 0.5, "ไม่มีข้อมูล", fontsize=14, ha="center", va="center")
        ax.set_title("รายได้รายเดือน")
        return fig

    # แปลงเดือนเป็นชื่อภาษาไทย
    thai_months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
    months = [thai_months[m['month'].month - 1] for m in data]
    values = [m['total'] for m in data]

    # สร้างเส้นกราฟ
    ax.plot(months, values, marker='o', markersize=8, linewidth=3, 
           color=THEME_COLORS['secondary'], markerfacecolor='white')
    
    # เติมพื้นที่ใต้เส้นกราฟ
    ax.fill_between(months, values, color=THEME_COLORS['secondary'], alpha=0.2)
    
    # เพิ่มค่าตัวเลขเหนือจุด
    for i, v in enumerate(values):
        ax.text(i, v + max(values)*0.05, f'{int(v):,} ฿', 
               ha='center', va='bottom', fontweight='bold')

    # ปรับแต่งแกนและเส้นตาราง
    ax.set_xlabel("เดือน", labelpad=10)
    ax.set_ylabel("รายได้ (บาท)", labelpad=10)
    ax.set_title("รายได้รายเดือน", pad=15)
    
    # ฟอร์แมตแกน y เป็นรูปแบบเงินบาท
    formatter = FuncFormatter(money_fmt)
    ax.yaxis.set_major_formatter(formatter)
    
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    
    return fig

# สร้างหน้าแดชบอร์ดด้วย Gradio
def create_dashboard():
    data = fetch_dashboard_data()
    
    # ฟอร์แมตตัวเลขให้สวยงาม
    income_today = f"{data['total_income_today']:,}"
    income_month = f"{data['total_income_month']:,}"
    income_all = f"{data['total_income_all']:,}"
    
    # ข้อความสรุปสถิติ
    summary_html = f"""
    <div style="display: flex; flex-wrap: wrap; gap: 20px; justify-content: space-between;">
        <div style="background-color: #EDF2FF; border-radius: 12px; padding: 15px; min-width: 200px; flex: 1;">
            <h3 style="margin: 0; font-size: 18px; color: #4F6CD9;">💰 รายได้วันนี้</h3>
            <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: bold;">{income_today} ฿</p>
        </div>
        
        <div style="background-color: #E6FBF8; border-radius: 12px; padding: 15px; min-width: 200px; flex: 1;">
            <h3 style="margin: 0; font-size: 18px; color: #29B695;">📅 รายได้เดือนนี้</h3>
            <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: bold;">{income_month} ฿</p>
        </div>
        
        <div style="background-color: #FFF8E6; border-radius: 12px; padding: 15px; min-width: 200px; flex: 1;">
            <h3 style="margin: 0; font-size: 18px; color: #F5A623;">💼 รายได้ทั้งหมด</h3>
            <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: bold;">{income_all} ฿</p>
        </div>
    </div>
    """
    
    return summary_html

# สร้างอินเทอร์เฟซ Gradio
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue")) as iface:
    gr.Markdown(
        """
        # 🎯 แดชบอร์ดคลินิกทันตกรรม
        ### แสดงภาพรวมและสถิติการดำเนินงานของคลินิก
        """
    )
    
    # รายได้สรุป
    summary_html = gr.HTML(create_dashboard)
    
    with gr.Row():
        # กราฟรายได้รายเดือน
        gr.Markdown("### 📊 รายได้รายเดือน")
        monthly_revenue_chart = gr.Plot(plot_monthly_revenue(fetch_dashboard_data()["monthly_revenue"]))
    
    # ฟังก์ชันรีเฟรชข้อมูล
    def refresh_data():
        data = fetch_dashboard_data()
        return (
            create_dashboard(),
            plot_monthly_revenue(data["monthly_revenue"]),
        )
    
    # ปุ่มรีเฟรชข้อมูล
    refresh_btn = gr.Button("🔄 รีเฟรชข้อมูล", variant="primary")
    
    # กำหนดการทำงานของปุ่มรีเฟรช
    refresh_btn.click(
        fn=refresh_data,
        outputs=[summary_html, monthly_revenue_chart]
    )

# เริ่มใช้งาน Gradio
iface.launch()
