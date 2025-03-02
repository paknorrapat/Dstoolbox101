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
def plot_appointments_by_month(data):
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(THEME_COLORS['background'])

    if not data:
        ax.text(0.5, 0.5, "ไม่มีข้อมูล", fontsize=14, ha="center", va="center")
        ax.set_title("จำนวนการนัดหมายในแต่ละเดือน")
        return fig

    # แปลงเดือนเป็นชื่อภาษาไทย
    thai_months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
    months = [thai_months[m['month'].month - 1] for m in data]
    values = [m['total'] for m in data]

    # สร้างกราฟแท่งพร้อมเส้นแนวโน้ม
    bars = ax.bar(months, values, color=THEME_COLORS['primary'], alpha=0.8, width=0.6)
    
    # เพิ่มเส้นแนวโน้ม
    if len(values) > 1:
        ax.plot(months, values, 'o-', color=THEME_COLORS['accent'], linewidth=3, markersize=8, alpha=0.7)
    
    # เพิ่มค่าตัวเลขเหนือแท่ง
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}',
                ha='center', va='bottom', fontweight='bold')

    ax.set_xlabel("เดือน", labelpad=10)
    ax.set_ylabel("จำนวนการนัดหมาย", labelpad=10)
    ax.set_title("จำนวนการนัดหมายในแต่ละเดือน", pad=15)
    ax.grid(axis='y', linestyle='--', alpha=0.6)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    
    return fig

def plot_appointments_by_status(data):
    fig, ax = plt.subplots(figsize=(7, 7))
    fig.patch.set_facecolor(THEME_COLORS['background'])

    if not data:
        ax.text(0.5, 0.5, "ไม่มีข้อมูล", fontsize=14, ha="center", va="center")
        ax.set_title("สถานะการนัดหมาย")
        return fig

    # แปลงสถานะเป็นภาษาไทยที่สวยงาม
    status_mapping = {
        'completed': 'เสร็จสิ้น',
        'pending': 'รอดำเนินการ',
        'cancelled': 'ยกเลิก',
        'no_show': 'ไม่มาตามนัด',
        'rescheduled': 'เลื่อนนัด'
    }
    
    labels = [status_mapping.get(s['status'], s['status']) for s in data]
    values = [s['total'] for s in data]
    
    # สีที่สวยงามสำหรับพาย
    colors = ['#4F6CD9', '#29B695', '#FF7676', '#FFB36B', '#B898FF', '#6BBFFF']
    
    # ข้อมูลเพิ่มเติมสำหรับแสดงร้อยละและจำนวน
    total = sum(values)
    
    # แก้ไขจากตรงนี้ - ไม่ใช้การรับค่าแบบหลายตัวแปร
    pie = ax.pie(
        values, 
        labels=None,  # ไม่แสดงชื่อในพาย
        startangle=90, 
        counterclock=False,
        colors=colors[:len(values)],
        wedgeprops={'edgecolor': 'white', 'linewidth': 2, 'antialiased': True},
        textprops={'color': THEME_COLORS['text'], 'fontweight': 'bold'}
    )
    
    # รับค่า wedges จากผลลัพธ์
    wedges = pie[0]
    
    # สร้างตำนานด้านข้าง
    ax.legend(
        wedges, 
        [f"{l} ({v}, {v/total:.1%})" for l, v in zip(labels, values)],
        title="สถานะ",
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1)
    )
    
    ax.set_title("สถานะการนัดหมาย", pad=20)
    fig.tight_layout()
    
    return fig

def plot_revenue_by_treatment(data):
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(THEME_COLORS['background'])

    if not data:
        ax.text(0.5, 0.5, "ไม่มีข้อมูล", fontsize=14, ha="center", va="center")
        ax.set_title("รายได้ตามประเภทการรักษา")
        return fig

    # จำกัดจำนวนการแสดงผลไม่เกิน 10 รายการ
    if len(data) > 10:
        data = data[:10]
        
    labels = [t['appointment__treatment__treatmentName'] for t in data]
    values = [t['total_revenue'] for t in data]
    
    # สร้างกราดิเอนท์สีจากอ่อนไปเข้ม
    cm = plt.cm.get_cmap('GnBu')
    colors = [cm(1. * i / len(labels)) for i in range(len(labels))]

    # สร้างกราฟแท่งนอน
    bars = ax.barh(labels, values, color=colors, height=0.6)
    
    # เพิ่มค่าตัวเลขด้านขวาของแท่ง
    for bar in bars:
        width = bar.get_width()
        ax.text(width + (max(values) * 0.01), 
                bar.get_y() + bar.get_height()/2, 
                f'{int(width):,} ฿',
                ha='left', va='center', fontweight='bold')

    # ตั้งค่าการแสดงผลแกน
    ax.set_xlabel("รายได้ (บาท)", labelpad=10)
    ax.set_ylabel("ประเภทการรักษา", labelpad=10)
    ax.set_title("รายได้ตามประเภทการรักษา", pad=15)
    
    # ฟอร์แมตแกน x เป็นรูปแบบเงินบาท
    formatter = FuncFormatter(money_fmt)
    ax.xaxis.set_major_formatter(formatter)
    
    ax.grid(axis='x', linestyle='--', alpha=0.6)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    
    return fig

def plot_top_dentists(data):
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(THEME_COLORS['background'])

    if not data:
        ax.text(0.5, 0.5, "ไม่มีข้อมูล", fontsize=14, ha="center", va="center")
        ax.set_title("ทันตแพทย์ที่มีการนัดหมายมากที่สุด")
        return fig
        
    # จำกัดจำนวนการแสดงผลไม่เกิน 10 รายการ
    if len(data) > 10:
        data = data[:10]

    labels = [d['dentist__dentistName'] for d in data]
    values = [d['total'] for d in data]
    
    # คำนวณร้อยละ
    total = sum(values)
    percentages = [v/total*100 for v in values]

    # สร้างกราดิเอนท์สีจากอ่อนไปเข้ม
    cm = plt.cm.get_cmap('PuBu')
    colors = [cm(1. * i / len(labels)) for i in range(len(labels))]
    
    # สร้างกราฟแท่งนอน
    bars = ax.barh(labels, values, color=colors, height=0.6)
    
    # เพิ่มค่าตัวเลขด้านขวาของแท่ง
    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax.text(width + 0.3, 
                bar.get_y() + bar.get_height()/2, 
                f'{int(width)} ({percentages[i]:.1f}%)',
                ha='left', va='center', fontweight='bold')

    ax.set_xlabel("จำนวนการนัดหมาย", labelpad=10)
    ax.set_ylabel("ทันตแพทย์", labelpad=10)
    ax.set_title("ทันตแพทย์ที่มีการนัดหมายมากที่สุด", pad=15)
    ax.grid(axis='x', linestyle='--', alpha=0.6)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    
    return fig

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
    
    # คำนวณยอดรวมและร้อยละการเปลี่ยนแปลง
    try:
        if data["monthly_revenue"] and len(data["monthly_revenue"]) >= 2:
            current_month = data["monthly_revenue"][-1]['total']
            previous_month = data["monthly_revenue"][-2]['total']
            monthly_change_pct = ((current_month - previous_month) / previous_month * 100) if previous_month else 0
            monthly_change_icon = "📈" if monthly_change_pct >= 0 else "📉"
            monthly_change_color = "green" if monthly_change_pct >= 0 else "red"
        else:
            monthly_change_pct = 0
            monthly_change_icon = "➖"
            monthly_change_color = "gray"
    except (IndexError, KeyError):
        monthly_change_pct = 0
        monthly_change_icon = "➖"
        monthly_change_color = "gray"
    
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
            <p style="margin: 0; font-size: 14px; color: {monthly_change_color};">{monthly_change_icon} {monthly_change_pct:.1f}% จากเดือนก่อน</p>
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
    
    with gr.Tabs():
        with gr.TabItem("📊 การนัดหมาย"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 📅 จำนวนการนัดหมายรายเดือน")
                    appointments_by_month_chart = gr.Plot(plot_appointments_by_month(fetch_dashboard_data()["appointments_by_month"]))
                
                with gr.Column():
                    gr.Markdown("### 📝 สถานะการนัดหมาย")
                    appointments_by_status_chart = gr.Plot(plot_appointments_by_status(fetch_dashboard_data()["appointments_by_status"]))
        
        with gr.TabItem("💵 รายได้"):
            gr.Markdown("### 💰 รายได้ตามประเภทการรักษา")
            revenue_by_treatment_chart = gr.Plot(plot_revenue_by_treatment(fetch_dashboard_data()["revenue_by_treatment"]))
        
        with gr.TabItem("👩‍⚕️ ทันตแพทย์"):
            gr.Markdown("### 🦷 ทันตแพทย์ที่มีการนัดหมายมากที่สุด")
            top_dentists_chart = gr.Plot(plot_top_dentists(fetch_dashboard_data()["top_dentists"]))
    
    # ปุ่มรีเฟรชข้อมูล
    refresh_btn = gr.Button("🔄 รีเฟรชข้อมูล", variant="primary")
    
    # ฟังก์ชันรีเฟรชข้อมูล
    def refresh_data():
        data = fetch_dashboard_data()
        return (
            create_dashboard(),
            plot_appointments_by_month(data["appointments_by_month"]),
            plot_appointments_by_status(data["appointments_by_status"]),
            plot_revenue_by_treatment(data["revenue_by_treatment"]),
            plot_top_dentists(data["top_dentists"]),
            plot_monthly_revenue(data["monthly_revenue"])
        )
    
    # กำหนดการทำงานของปุ่มรีเฟรช
    refresh_btn.click(
        fn=refresh_data,
        outputs=[
            summary_html,
            appointments_by_month_chart,
            appointments_by_status_chart,
            revenue_by_treatment_chart,
            top_dentists_chart,
            monthly_revenue_chart
        ]
    )

# เริ่มใช้งาน Gradio
iface.launch()