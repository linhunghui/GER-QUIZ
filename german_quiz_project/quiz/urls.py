# quiz/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # 
    # 功能1 (使用者系統) - 已完成
    # 
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='quiz/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # 
    # 功能2 (程度選擇)
    # 
    # 我們將 home_view (登入後的首頁) 作為程度選擇頁
    path('', views.home_view, name='home'),

    # 
    # 功能4 (每日抽考)
    # 

    # 1. 開始測驗 (點擊 A1 後觸發, 負責準備題目)
    path('quiz/start/<str:level>/', views.start_quiz_view, name='start_quiz'),
    
    # 2. 測驗問題頁面 (顯示問題並檢查答案)
    #    (我們在下一步會實作這個 view)
    path('quiz/question/', views.quiz_question_view, name='quiz_question'),

    # 3. 測驗結果頁面 (顯示總分和錯誤)
    #    (我們之後會實作這個 view)
    path('quiz/results/', views.quiz_results_view, name='quiz_results'),

    # --- ***在這裡新增*** ---
    
    # 1. 開始 "Review" 測驗
    path('review/start/', views.start_review_view, name='start_review'),

    # 2. 清除錯誤紀錄 (清除記憶)
    path('review/clear/', views.clear_errors_view, name='clear_errors'),
    
    # --- ***新增結束*** ---
]