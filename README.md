ถ้าติด base  -->  conda deactivate
python -m venv env
env\Scripts\activate
cd Clinic101
pip install -r requirements.txt 
python manage.py makemigrations
python manage.py migrate

npm i -D daisyui@latest

เวลารัน เปิด 3  terminal
1   python manage.py tailwind start 
2   python gradio_dashboard.py ถ้าปกติ มันจะมี link gradio ให้เปิด แล้ว ก็อปลิงก์นั้น ไปเปลี่ยนใน second_dashboard.html   เปลี่ยนตรง src <iframe src="http://127.0.0.1:7860" width="100%" height="600px"></iframe>
3   python manage.py runserver



python manage.py createsuperuser
