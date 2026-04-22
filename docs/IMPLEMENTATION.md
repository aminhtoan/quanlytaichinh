# Ke hoach trien khai da hoan thanh

## 1) MVP
- Auth: dang ky, dang nhap, lay thong tin nguoi dung.
- Giao dich: tao, sua, xoa, danh sach va tong hop so du.

## 2) Kien truc
- Backend FastAPI theo module: `routers`, `services`, `schemas`, `db`.
- Frontend React + Vite, su dung 1 dashboard gom: auth, giao dich, NLP, AI.

## 3) AI/NLP/OCR
- NLP parser cho cau tu nhien tieng Viet de tao giao dich.
- AI insight gom ty le chi tieu, canh bao bat thuong, goi y tiet kiem.
- Chatbot dung Gemini neu co API key, fallback local neu chua cau hinh.
- OCR hoa don qua Tesseract, tra ve text + goi y giao dich.

## 4) Bao mat va deploy
- JWT auth + hash password (`bcrypt`).
- Tach cau hinh qua `.env` va loai bo hard-coded secret.
- Dockerfile cho backend/frontend va `docker-compose.yml` cho local stack.
