# Create your models here.
# quiz/models.py
from django.db import models
# 匯入 Django 內建的使用者模型，這樣我們才能建立關聯
from django.contrib.auth.models import User 

# 德文程度的選項 (A1, A2, ...)
class Level(models.TextChoices):
    A1 = 'A1', 'A1'
    A2 = 'A2', 'A2'
    B1 = 'B1', 'B1'
    B2 = 'B2', 'B2'
    C1 = 'C1', 'C1'
    C2 = 'C2', 'C2'

# 
# 1. 儲存單字的資料表
# 
class Vocabulary(models.Model):
    # 關聯到您 JSON 中的 'id'，但不一定是必要的，
    # Django 會自動建立一個 'id' 欄位作為主鍵 (Primary Key)
    # original_id = models.IntegerField(unique=True, null=True, blank=True) # 您可以選擇是否保留舊的 ID

    # 德文內容 (使用 TextField 來容納換行符號 \n)
    german_content = models.TextField(verbose_name="德文內容")
    
    # 英文內容 (同樣使用 TextField)
    english_content = models.TextField(verbose_name="英文內容")

    # 程度 (A1, A2...)
    level = models.CharField(
        max_length=2,
        choices=Level.choices,
        default=Level.A1, # 預設為 A1
        verbose_name="語言程度"
    )

    def __str__(self):
        # 在 Django 後台顯示時，我們取德文內容的前20個字
        return f"[{self.level}] {self.german_content[:20]}..."
    # --- ***在這裡新增*** ---
    @property
    def clean_english_word(self):
        """
        輔助功能：
        從 "back \nWhen are you coming back?" 
        中回傳乾淨的 "back"
        """
        try:
            # (舊) return self.english_content.split('\n')[0].strip()
            
            # (新) 我們告訴 python 在 "反斜線+n" 的「文字組合」上分割
            return self.english_content.split('\\n')[0].strip() 
        except:
            return ""
    # --- ***新增結束*** ---    
    class Meta:
        verbose_name = "單字"
        verbose_name_plural = "單字庫"


# 
# 2. 儲存使用者錯誤紀錄的資料表 (功能4)
# 
class UserError(models.Model):
    # 關聯到使用者 (多對一：一個使用者可以有多筆錯誤紀錄)
    # on_delete=models.CASCADE 表示如果使用者被刪除，他的錯誤紀錄也一併刪除
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="使用者")

    # 關聯到單字 (多對一：一個單字可以被多個使用者答錯)
    vocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE, verbose_name="錯誤單字")

    # 錯誤次數 (可以選擇性加入，未來可用來加強常錯的題目)
    # error_count = models.IntegerField(default=1, verbose_name="錯誤次數")

    # 紀錄時間
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="紀錄時間")

    def __str__(self):
        return f"{self.user.username} 錯了 {self.vocabulary.german_content[:10]}..."
    
    class Meta:
        verbose_name = "使用者錯誤紀錄"
        verbose_name_plural = "使用者錯誤紀錄"
        # 建立一個「聯合唯一索引」，確保同一個使用者對同一個單字的錯誤只會被記錄一次
        # 這樣 "Review" 模式才不會有重複的題目
        unique_together = ('user', 'vocabulary')