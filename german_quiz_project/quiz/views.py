# quiz/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login 
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# --- (修改) 匯入我們需要的模型 ---
from .models import Vocabulary, UserError, Level
# --- (新增) 匯入 random 模組 ---
import random 

# 
# 1. 註冊視圖 (已完成, 不需修改)
# 
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home') 
    else:
        form = UserCreationForm()
    return render(request, 'quiz/register.html', {'form': form})

# 
# 2. 首頁視圖 (功能2: 程度選擇) - (已完成, 不需修改)
# 
@login_required
def home_view(request):
    available_levels = Vocabulary.objects.values_list('level', flat=True).distinct().order_by('level')
    context = {
        'available_levels': available_levels
    }
    return render(request, 'quiz/home.html', context)

# 
# 3. 開始測驗視圖 (功能4 - Part 1) - ***大幅修改***
# 
@login_required
def start_quiz_view(request, level):
    # 1. 抓取 10 個隨機問題 (不變)
    questions_qs = Vocabulary.objects.filter(level=level).order_by('?')[:30]

    # 抓取該等級的所有單字，用來當作誘答選項池
    all_words_pool = list(Vocabulary.objects.filter(level=level))

    serialized_questions = []
    
    for q in questions_qs:
        # --- (修改) 使用我們在 models.py 建立的輔助功能 ---
        correct_answer = q.clean_english_word

        # --- (新增) 產生 3 個誘答選項 ---
        distractors_pool = [
            word.clean_english_word 
            for word in all_words_pool 
            if word.id != q.id and word.clean_english_word != correct_answer
        ]
        
        # 從誘答選項池中隨機選 3 個
        # (使用 set 確保選項不重複)
        distractors = random.sample(list(set(distractors_pool)), 3)

        # 組合 1 個正確 + 3 個錯誤 選項
        choices = distractors + [correct_answer]
        # 隨機打亂選項順序
        random.shuffle(choices)

        serialized_questions.append({
            'id': q.id, 
            'german_content': q.german_content, 
            'english_answer': correct_answer,   # 正確答案 (字串)
            'full_english_hint': q.english_content,
            'choices': choices,                 # <-- (新增) 選擇題選項
        })

    # 3. 初始化 Session (不變)
    request.session['quiz_questions'] = serialized_questions
    request.session['current_question_index'] = 0
    request.session['score'] = 0
    request.session['mistakes'] = []

    return redirect('quiz_question')


# 
# 4. 測驗問題視圖 (功能4 - Part 2) - ***修改***
# 
@login_required
def quiz_question_view(request):
    # 1. 從 Session 獲取測驗狀態 (不變)
    try:
        questions = request.session['quiz_questions']
        current_index = request.session['current_question_index']
        score = request.session['score']
        mistakes = request.session['mistakes']
    except KeyError:
        return redirect('home')

    total_questions = len(questions)

    # 2. 檢查測驗是否已結束 (不變)
    if current_index >= total_questions:
        return redirect('quiz_results')

    # 3. 獲取目前題目 (不變)
    current_question = questions[current_index]

    # --- (修正 1) 在 View 中處理字串切割 ---
    german_content = current_question['german_content']
    # (舊) parts = german_content.split('\n', 1)
    # (新) 同樣，在 "反斜線+n" 的「文字組合」上分割
    parts = german_content.split('\\n', 1) 
    german_word = parts[0]
    german_example = parts[1] if len(parts) > 1 else ""
    # --- (修正 1 結束) ---
    
    choices = current_question['choices']


    # 4. 處理 POST 請求 (使用者提交答案)
    if request.method == 'POST':
        
        user_answer = request.POST.get('choice', '').strip() 
        correct_answer = current_question['english_answer'].strip()

        is_correct = False
        feedback = ""

        # 5. 檢查答案
        if user_answer.lower() == correct_answer.lower():
            is_correct = True
            feedback = "✅ 正確！"
            request.session['score'] = score + 1
        else:
            # --- (修正 2) 處理反饋中的 \n ---
            # (舊) full_answer_hint = current_question['full_english_hint']
            # (新) 將 "反斜線+n" (文字) 替換為 "換行符號"
            full_answer_hint = current_question['full_english_hint'].replace('\\n', '\n') 
            
            feedback = f"❌ 錯誤... 正確答案是: \n{full_answer_hint}"
            # --- (修正 2 結束) ---

            mistakes.append(current_question)
            request.session['mistakes'] = mistakes
            # --- ***在這裡加入檢查*** ---
            is_review = request.session.get('is_review_mode', False)
            if not is_review: # 如果「不是」Review 模式，才記錄錯誤
                try:
                    vocab_obj = Vocabulary.objects.get(id=current_question['id'])
                    UserError.objects.get_or_create(
                        user=request.user,
                        vocabulary=vocab_obj
                    )
                except Vocabulary.DoesNotExist:
                    print(f"錯誤：找不到 ID 為 {current_question['id']} 的單字")
            # --- ***檢查結束*** ---            
            try:
                vocab_obj = Vocabulary.objects.get(id=current_question['id'])
                UserError.objects.get_or_create(
                    user=request.user,
                    vocabulary=vocab_obj
                )
            except Vocabulary.DoesNotExist:
                print(f"錯誤：找不到 ID 為 {current_question['id']} 的單字")

        # 6. 更新 Session 中的題號 (不變)
        request.session['current_question_index'] = current_index + 1
        request.session.modified = True 

        # 7. 渲染 "反饋" 頁面 (不變)
        context = {
            'german_word': german_word,       
            'german_example': german_example, 
            'choices': choices,               
            'feedback': feedback,
            'is_correct': is_correct,
            'is_feedback': True, 
            'current_progress': current_index + 1,
            'total_questions': total_questions
        }
        return render(request, 'quiz/quiz_question.html', context)

        # 5. 檢查答案 ( .lower() 不區分大小寫)
        if user_answer.lower() == correct_answer.lower():
            is_correct = True
            feedback = "✅ 正確！"
            request.session['score'] = score + 1
        else:
            feedback = f"❌ 錯誤... 正確答案是: {correct_answer}"
            mistakes.append(current_question)
            request.session['mistakes'] = mistakes
            
            try:
                vocab_obj = Vocabulary.objects.get(id=current_question['id'])
                UserError.objects.get_or_create(
                    user=request.user,
                    vocabulary=vocab_obj
                )
            except Vocabulary.DoesNotExist:
                print(f"錯誤：找不到 ID 為 {current_question['id']} 的單字")

        # 6. 更新 Session 中的題號 (不變)
        request.session['current_question_index'] = current_index + 1
        request.session.modified = True 

        # 7. 渲染 "反饋" 頁面 - ***修改***
        context = {
            'german_word': german_word,       
            'german_example': german_example, 
            'choices': choices,               # <-- (新增) 把選項傳回去
            'feedback': feedback,
            'is_correct': is_correct,
            'is_feedback': True, 
            'current_progress': current_index + 1,
            'total_questions': total_questions
        }
        return render(request, 'quiz/quiz_question.html', context)

    # 5. 處理 GET 請求 (顯示新題目) - ***修改***
    context = {
        'german_word': german_word,       
        'german_example': german_example, 
        'choices': choices,               # <-- (新增) 把選項傳過去
        'is_feedback': False,
        'current_progress': current_index + 1,
        'total_questions': total_questions
    }
    return render(request, 'quiz/quiz_question.html', context)


# 
# 5. 測驗結果視圖 (功能4 - Part 3) - (保持空殼)
# 
# 5. 測驗結果視圖 (功能4 - Part 3) - ***修改***
# 
@login_required
def quiz_results_view(request):
    # 1. 從 Session 獲取最終的測驗資料
    try:
        score = request.session['score']
        total_questions = len(request.session['quiz_questions'])
        
        # 獲取錯誤列表，並處理 \n (文字)
        mistakes_raw = request.session.get('mistakes', [])
        mistakes_processed = []
        for item in mistakes_raw:
            mistakes_processed.append({
                # 將 "gehen \nJetzt..." 替換為 "gehen" 和 "Jetzt..."
                'german_word': item['german_content'].split('\\n')[0],
                'german_example': item['german_content'].split('\\n')[1] if '\\n' in item['german_content'] else '',
                
                # 將 "expensive \nThat is..." 替換為 "expensive" 和 "That is..."
                'english_word': item['full_english_hint'].split('\\n')[0],
                'english_example': item['full_english_hint'].split('\\n')[1] if '\\n' in item['full_english_hint'] else '',
            })

    except KeyError:
        # 如果 session 資料遺失 (例如使用者在結果頁按 F5 重整)
        # 導回首頁，避免錯誤
        return redirect('home')

    # 2. (重要) 清除 Session 中的測驗資料
    #    這樣使用者回到首頁才能開始「新」的測驗
    #    我們保留 'score' 和 'mistakes' 傳給模板
    request.session.pop('quiz_questions', None)
    request.session.pop('current_question_index', None)
    request.session.pop('mistakes', None)
    request.session.pop('score', None)

    # 3. 準備 context 並渲染模板
    context = {
        'score': score,
        'total_questions': total_questions,
        'mistakes': mistakes_processed, # 傳入處理過的錯誤列表
    }
    return render(request, 'quiz/quiz_results.html', context)
# 6. 開始 "Review" 測驗 (功能4 - Review) - ***新增***
# 
@login_required
def start_review_view(request):
    # 1. 找出這位使用者 (request.user) 所有的錯誤紀錄
    user_errors = UserError.objects.filter(user=request.user)

    # 2. 從錯誤紀錄中，取出對應的 "單字" (Vocabulary) 物件
    #    'vocabulary' 是我們在 UserError model 中定義的欄位名稱
    error_vocab_list = [error.vocabulary for error in user_errors]

    # 3. 檢查是否有錯誤的單字
    if not error_vocab_list:
        # 如果沒有錯誤，導回首頁並附上一個提示訊息
        # (我們下一步會在 home.html 顯示這個訊息)
        from django.contrib import messages
        messages.info(request, '您目前沒有任何錯誤紀錄可供複習！')
        return redirect('home')
    
    # 4. 如果錯誤單字超過 10 個，隨機選 10 個
    if len(error_vocab_list) > 30:
        questions_qs = random.sample(error_vocab_list, 30)
    else:
        # 如果少於 10 個，就全部複習
        questions_qs = error_vocab_list
        # (可選) 再次打亂順序
        random.shuffle(questions_qs)

    # 5. (重要) 我們需要抓取「所有」單字來當作誘答選項池
    #    (如果只用錯誤單字當選項池，選項會太少或都是錯的)
    #    我們假設複習 A1 的錯誤，誘答選項也從 A1 來
    #    (簡易作法：抓取 A1 等級的單字)
    all_words_pool = list(Vocabulary.objects.filter(level=Level.A1))

    # --- (以下邏輯與 start_quiz_view 完全相同) ---
    
    serialized_questions = []
    for q in questions_qs:
        correct_answer = q.clean_english_word # 使用 .clean_english_word

        distractors_pool = [
            word.clean_english_word 
            for word in all_words_pool 
            if word.id != q.id and word.clean_english_word != correct_answer
        ]
        
        # 確保誘答選項池足夠 (至少 3 個)
        if len(set(distractors_pool)) < 3:
            # 如果 A1 選項池不夠，就從所有單字中抓 (B計畫)
            all_words_pool_global = list(Vocabulary.objects.all())
            distractors_pool = [
                word.clean_english_word 
                for word in all_words_pool_global 
                if word.id != q.id and word.clean_english_word != correct_answer
            ]

        distractors = random.sample(list(set(distractors_pool)), 3)
        choices = distractors + [correct_answer]
        random.shuffle(choices)

        serialized_questions.append({
            'id': q.id, 
            'german_content': q.german_content, 
            'english_answer': correct_answer,
            'full_english_hint': q.english_content,
            'choices': choices,
        })

    # 6. 初始化 Session
    request.session['quiz_questions'] = serialized_questions
    request.session['current_question_index'] = 0
    request.session['score'] = 0
    request.session['mistakes'] = []

    # 7. (重要) 我們新增一個 flag，告訴結果頁這是 "Review" 模式
    #    這樣在 Review 中答錯的題目，才不會被再次存入 UserError
    request.session['is_review_mode'] = True # <-- (可選，但建議)

    return redirect('quiz_question')


# 
# 7. 清除錯誤紀錄 (功能4 - Clear) - ***新增***
# 
@login_required
def clear_errors_view(request):
    # (安全起見，使用 POST 請求來刪除資料)
    if request.method == 'POST':
        # 刪除這位使用者 (request.user) 所有的 UserError 紀錄
        UserError.objects.filter(user=request.user).delete()
        
        # (可選) 增加一個成功訊息
        from django.contrib import messages
        messages.success(request, '您的所有錯誤紀錄已成功清除！')

    # 不論是 GET 還是 POST，最後都導回首頁
    return redirect('home')

# --- (補充) 修改 quiz_question_view (避免重複記錄錯誤) ---
# 
# 為了避免在 "Review" 模式中答錯，又把錯誤存回去
# 我們要稍微修改一下 quiz_question_view 的 POST 邏輯
# 
# ... 找到 quiz_question_view ...
#
#       if user_answer.lower() == correct_answer.lower():
#           ...
#       else:
#           ...
#           mistakes.append(current_question)
#           request.session['mistakes'] = mistakes
#           
#           # --- ***在這裡加入檢查*** ---
#           is_review = request.session.get('is_review_mode', False)
#           if not is_review: # 如果「不是」Review 模式，才記錄錯誤
#               try:
#                   vocab_obj = Vocabulary.objects.get(id=current_question['id'])
#                   UserError.objects.get_or_create(
#                       user=request.user,
#                       vocabulary=vocab_obj
#                   )
#               except Vocabulary.DoesNotExist:
#                   print(f"錯誤：找不到 ID 為 {current_question['id']} 的單字")
#           # --- ***檢查結束*** ---
#