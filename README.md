# 德文測字網站

因女友要讀德文所以 Vibecode 了德文測字網站包含 A1/A2 後續會依照女友需要增加 B1/B2 及混合測驗功能，假如好用的話請跟女友說聲謝謝並請他好好學習（本人絕對沒有被脅迫）。

## 功能介紹

### 1. 單字分級測試

![功能](https://github.com/linhunghui/GER-QUIZ/blob/main/%E5%8A%9F%E8%83%BD1.png)

### 2. 錯誤提示

![功能](https://github.com/linhunghui/GER-QUIZ/blob/main/%E5%8A%9F%E8%83%BD2.png)

### 3. 錯誤複習

![功能](https://github.com/linhunghui/GER-QUIZ/blob/main/%E5%8A%9F%E8%83%BD3.png)

# 使用說明

## 1. 複製專案並設定

```bash
git clone https://github.com/linhunghui/GER-QUIZ.git
cd GER-QUIZ

# 複製 .env 範例並填入實際值
cp .env.example .env
# 編輯 .env，設定以下必要變數：
#   SECRET_KEY: 用此命令生成新密鑰
#              python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
#   DEBUG: 開發時設為 1，生產環境設為 0
#   ALLOWED_HOSTS: 你的域名與 IP，逗號分隔
#   CSRF_TRUSTED_ORIGINS: 允許跨域請求的來源，逗號分隔
#   DB_PASS: 資料庫密碼（務必修改）
```

## 2. HTTP 快速啟動（推薦開發或內部使用）

預設設定使用 HTTP。無需任何額外設定，直接啟動：

```bash
docker compose up --build -d
```

檢查容器狀態：

```bash
docker compose ps
docker compose logs -f web
```

訪問應用程式：

- `http://localhost`（本機）
- `http://your-machine-ip`（其他機器訪問）

## 3. HTTPS 設定（生產環境推薦）

### 3.1 準備 SSL 憑證

SSL 憑證需放在 `local/ssl/` 目錄：

```bash
mkdir -p local/ssl
```

**選項 A：使用現有憑證**

```bash
# 複製你已有的 SSL 憑證
cp /path/to/your/certificate.pem local/ssl/server.pem
cp /path/to/your/private.key local/ssl/server.key
```

**選項 B：使用 Let's Encrypt（推薦，免費）**

```bash
# 安裝 certbot（若未安裝）
# Ubuntu/Debian:
sudo apt-get install certbot

# macOS:
brew install certbot

# 生成憑證
certbot certonly --standalone -d your-domain.com

# 複製憑證到本專案
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem local/ssl/server.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem local/ssl/server.key

# 修改權限
sudo chown $USER:$USER local/ssl/server.*
```

### 3.2 啟用 HTTPS 配置

編輯 `nginx/conf.d/german_quiz.conf`，找到註解的 `# server {` 區塊（監聽 443 ），取消註解所有行：

**修改前：**

```nginx
# server {
#     listen 443 ssl http2;
#     server_name your-domain.com www.your-domain.com;
#     ...
# }
```

**修改後：**

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    ...
}
```

**重要**：修改 `server_name` 為你的實際域名。

### 3.3 （可選）啟用 HTTP → HTTPS 自動轉向

在同一個檔案的最後，取消註解最後一個 `# server {` 區塊（監聽 80 ），以將所有 HTTP 流量自動轉向 HTTPS：

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        return 301 https://$host$request_uri;
    }
}
```

### 3.4 重新啟動容器

```bash
docker compose down
docker compose up --build -d
docker compose logs -f nginx
```

訪問應用程式：

```
https://your-domain.com
```

## 4. 常用命令

### 檢查容器狀態與日誌

```bash
# 列出所有容器及狀態
docker compose ps

# 檢視 web 容器（Django/Gunicorn）日誌
docker compose logs -f web

# 檢視 nginx 容器日誌
docker compose logs -f nginx

# 檢視 db 容器（MySQL）日誌
docker compose logs -f db
```

### 停止與清理

```bash
# 停止容器，保留資料
docker compose down

# 完全清理（含資料庫資料，慎用！）
docker compose down -v

# 重建映像並啟動
docker compose up --build -d
```

### 進入容器執行命令

```bash
# 在 web 容器中執行 Django 命令
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell

# 在 db 容器中進入 MySQL
docker compose exec db mysql -u darren -p vocab_quiz
```

### 管理後台與管理員專用摘要頁

- Django 管理介面（Admin）： `http://localhost:8000/admin/` （需 `is_staff` 或 superuser）
- 我新增的管理員專用摘要頁（需 `is_staff`）： `http://localhost:8000/staff/attempts/`

註：若使用者尚未為 staff，可在主機上執行：

```bash
docker compose exec web python manage.py shell -c "from django.contrib.auth.models import User; u=User.objects.get(username='YOUR_USERNAME'); u.is_staff=True; u.save()"
```

### 需要重啟 Docker 嗎？

- 只修改內容（templates、靜態檔）且您有把專案原始碼掛載到容器（`volumes` 映射），通常不需要重建映像，只要重啟容器或讓變更自動生效即可。
- 若您是使用本專案預設的方式（沒有把 `german_quiz_project/` 掛載到容器），那麼每次修改 Python 代碼或新增模型、管理後台程式時，需重建映像並重啟服務：

```bash
docker compose up --build -d
```

- 若只是套用資料庫遷移（migrations）或建立 superuser，無需重建映像，只要在容器內執行相對應的管理命令：

```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

- 若您更新環境變數（`.env`）或 nginx 設定，建議使用：

```bash
docker compose down
docker compose up --build -d
```

## 5. 目錄結構說明

```
ger-quiz/
├── german_quiz_project/      # Django 應用程式原始碼
├── nginx/
│   └── conf.d/
│       └── german_quiz.conf  # Nginx 反向代理設定（支持 HTTP 與可選 HTTPS）
├── local/                     # 敏感資料目錄（選用）
│   ├── .gitkeep
│   └── ssl/
│       ├── server.pem        # SSL 憑證公鑰（若啟用 HTTPS）
│       └── server.key        # SSL 憑證私鑰（若啟用 HTTPS）
├── mysql/                     # MySQL 初始化 SQL 檔案
├── mysql_data/                # MySQL 資料目錄（不上傳 Git）
├── Dockerfile                # Docker 映像構建設定
├── docker-compose.yaml       # 服務編排設定
├── entrypoint.sh             # 容器啟動指令
├── requirements.txt          # Python 依賴
├── .env.example              # 環境變數範本
├── .gitignore
└── README.md
```

## 6. 環境變數說明

見 `.env.example` 檔案。主要變數：

| 變數                   | 說明                       | 預設值                                    |
| ---------------------- | -------------------------- | ----------------------------------------- |
| `SECRET_KEY`           | Django 密鑰（務必改變）    | `django-insecure-change-me-in-production` |
| `DEBUG`                | 除錯模式（0=關閉, 1=開啟） | `1`                                       |
| `ALLOWED_HOSTS`        | 允許的主機名（逗號分隔）   | `localhost,127.0.0.1`                     |
| `CSRF_TRUSTED_ORIGINS` | CSRF 信任來源（逗號分隔）  | `http://localhost`                        |
| `DB_NAME`              | 資料庫名稱                 | `vocab_quiz`                              |
| `DB_USER`              | 資料庫用戶                 | `darren`                                  |
| `DB_PASS`              | 資料庫密碼                 | `change-me`                               |
| `DB_HOST`              | 資料庫主機                 | `db`                                      |
| `DB_PORT`              | 資料庫埠                   | `3306`                                    |

## 7. 常見問題

**Q: 我只想用 HTTP，不需要 HTTPS，要改什麼？**

A: 不用改！預設就是 HTTP。直接 `docker compose up --build -d`，訪問 `http://localhost` 或你的機器 IP 即可。

---

**Q: 如何啟用 HTTPS？**

A: 參見上面「HTTPS 設定」章節。步驟簡述：

1. 把 SSL 憑證放到 `local/ssl/server.pem` 和 `local/ssl/server.key`
2. 編輯 `nginx/conf.d/german_quiz.conf`，取消註解 HTTPS 區塊
3. 改 `server_name` 為你的域名
4. 重啟容器：`docker compose down && docker compose up --build -d`

---

**Q: Nginx 回傳 502 Bad Gateway**

A: 通常是 web 容器（Gunicorn）未就緒。檢查日誌：

```bash
docker compose logs -f web
```

確認 Gunicorn 是否成功啟動，或是否有資料庫連線錯誤。

---

**Q: 資料庫連線失敗 ("Can't connect to MySQL server")**

A: 檢查以下幾點：

1. `.env` 中的 `DB_*` 設定是否正確
2. `db` 容器是否已啟動：`docker compose ps`
3. 資料庫是否通過健康檢查：`docker compose logs db`
4. 稍等數秒讓資料庫完全啟動後重試

---

**Q: 靜態檔案（CSS/JS）未加載**

A: 檢查 Django 靜態檔是否已收集：

```bash
docker compose exec web python manage.py collectstatic --noinput
```

檢查 nginx 日誌是否有路徑錯誤。

---

**Q: 如何重新初始化資料庫？**

A:

```bash
# 刪除資料庫容器與資料（慎用！）
docker compose down -v

# 重新建立並啟動
docker compose up --build -d

# 容器啟動時會自動執行 migrations
docker compose logs -f web
```

---

**Q: 如何在不同機器上部署？**

A:

1. `git clone` 本倉庫
2. `cp .env.example .env` 並編輯必要變數（SECRET_KEY、DB_PASS、ALLOWED_HOSTS 等）
3. 若需 HTTPS，把 SSL 憑證複製到 `local/ssl/`，並在 `nginx/conf.d/german_quiz.conf` 中取消註解 HTTPS 區塊
4. `docker compose up --build -d`
5. 訪問你的應用程式

---

## 8. 備份與還原

### 備份資料庫

```bash
# 導出 MySQL 資料庫
docker compose exec db mysqldump -u admin -p vocab_quiz > backup.sql

# 輸入密碼時用你在 .env 中設定的 DB_PASS
```

### 還原資料庫

```bash
# 導入 SQL 檔案
docker compose exec -T db mysql -u admin -p vocab_quiz < backup.sql
```

---

有問題或建議，歡迎提交 Issue 或 PR！
