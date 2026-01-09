# config/urls.py
from django.contrib import admin
from django.urls import path, include  # <-- 記得匯入 'include'

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 告速 Django：所有進到網站的請求 (空字串 '')
    # 都轉交給 'quiz.urls' 檔案去處理
    path('', include('quiz.urls')), 
]