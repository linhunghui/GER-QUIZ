# import_from_sql.py (V2 - 已修正 Bug)
import os
import django
import re

# --- 設定 Django 環境 ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
# --- 設定結束 ---

# 匯入我們在 models.py 中定義的模型
from quiz.models import Vocabulary, Level

# 您的 SQL 檔案路徑 (請確保路徑正確)
SQL_FILE_PATH = './vocab_quiz.sql' 

# 
# (V2) 修正後的解析器
# 
def parse_sql_inserts(filename):
    print(f"正在讀取 {filename}...")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        # (V2 修正) 尋找 INSERT 語句。
        # 這次我們使用更穩健的方式，尋找從 'VALUES' 開始，
        # 一直到 '...);' 結尾的整個區塊。
        # re.DOTALL 讓 '.' 可以匹配換行符號
        insert_pattern = re.compile(r"INSERT INTO `words` VALUES(.*?)\);", re.DOTALL)
        
        blocks = insert_pattern.findall(content)
        
        if not blocks:
            print("錯誤：在 .sql 檔案中找不到 'INSERT INTO `words` VALUES ...' 語句。")
            return []

        # 假設所有的 'INSERT' 都在第一個 block 中
        data_block = blocks[0]

        # (V2 修正) 這是更強大的正則表達式，用來解析 (id, 'german', 'english')
        # 它可以正確處理字串中包含的 ' (跳脫引號) 和 ; (分號)
        # 
        # r"\((\d+),"                        -> 匹配 (ID,
        # r"'((?:[^'\\]|\\.)*)',"             -> 匹配 '德文內容' (允許 \' )
        # r"'((?:[^'\\]|\\.)*)'\)"            -> 匹配 '英文內容' (允許 \' )
        value_pattern = re.compile(r"\((\d+),'((?:[^'\\]|\\.)*)','((?:[^'\\]|\\.)*)'\)") 

        all_inserts = []
        matches = value_pattern.findall(data_block)

        for match in matches:
            # match[0] = id (我們現在不需要了)
            # match[1] = german_word
            # match[2] = english_word
            
            # 處理 SQL 檔案中的 ' \' ' (跳脫引號)
            german_word = match[1].replace(r"\'", r"'").replace(r'\"', r'"')
            english_word = match[2].replace(r"\'", r"'").replace(r'\"', r'"')
            
            all_inserts.append((german_word, english_word))
        
        return all_inserts

    except FileNotFoundError:
        print(f"錯誤：找不到 SQL 檔案 '{filename}'")
        return []
    except Exception as e:
        print(f"讀取或解析檔案時發生錯誤: {e}")
        return []

def load_vocabulary():
    print("開始從 .sql 檔案匯入 A1 單字 (V2)...")
    
    # 步驟 1: 從 .sql 檔案解析資料
    words_to_import = parse_sql_inserts(SQL_FILE_PATH)
    
    if not words_to_import:
        print("沒有從 .sql 檔案中解析到任何單字。停止匯入。")
        return

    print(f"從 .sql 檔案中成功解析到 {len(words_to_import)} 筆單字。")
    print("--- 開始匯入到 Django 資料庫 ---")

    count_new = 0
    count_skipped = 0
    
    # 步驟 2: 將資料匯入到 Django 的 'quiz_vocabulary' 資料表
    for german_word, english_word in words_to_import:
        
        # 使用 get_or_create 避免重複建立
        # Django 會檢查德文內容是否已存在
        obj, created = Vocabulary.objects.get_or_create(
            german_content=german_word,
            defaults={
                'english_content': english_word,
                'level': Level.A1  # <-- 關鍵！我們將這些單字全部設為 A1
            }
        )

        if created:
            count_new += 1
            if count_new % 50 == 0: # 每 50 筆印一次
                print(f"  已新增 {count_new} 筆...")
        else:
            # 如果 'created' 是 False，表示這筆資料 (那 38 筆) 已經存在
            count_skipped += 1

    print("\n匯入完成！")
    print(f"  成功新增: {count_new} 筆 A1 單字。")
    print(f"  重複跳過: {count_skipped} 筆 (這包含您上次匯入的 38 筆)。")

# --- 執行主程式 ---
if __name__ == "__main__":
    load_vocabulary()