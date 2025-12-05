FROM nginx:1.25-alpine

# 刪除預設 Nginx 靜態頁面
RUN rm -rf /usr/share/nginx/html/*

# 把你的前端檔案（index.html, script.js, style.css...）複製進去
COPY . /usr/share/nginx/html

# 設定 Nginx config（等一下我們會加 gateway）
COPY nginx.conf /etc/nginx/conf.d/default.conf
