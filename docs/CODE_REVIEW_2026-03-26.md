# Code Review Report (2026-03-26)

## Phạm vi review
- Frontend: luồng đăng nhập, API client, dashboard sau khi tách component.
- Backend: auth, transaction, cấu hình bảo mật, lớp truy cập DB.
- Trạng thái build/check tại thời điểm review: không có lỗi compile/lint.

## Điểm tốt
- Dashboard đã được tách thành nhiều component rõ ràng, dễ bảo trì hơn.
- Form/handler nghiệp vụ đầy đủ cho các module chính (transactions, wallets, budgets, subscriptions, investments, debts, AI).
- Build frontend thành công, code hiện tại chạy ổn định ở mức chức năng chính.

## Vấn đề cần ưu tiên xử lý

### 1) [Critical] Secret mặc định yếu trong cấu hình
**Vị trí:** `backend/app/core/config.py`

- `secret_key` đang có default là `"change_me"`.
- Nếu triển khai mà quên set biến môi trường, JWT có nguy cơ bị giả mạo.

**Khuyến nghị:**
- Bắt buộc `SECRET_KEY` trong môi trường production (không cho phép fallback yếu).
- Validate khi startup: nếu secret yếu/mặc định thì raise lỗi để chặn chạy server.

---

### 2) [High] Đăng ký chưa kiểm tra trùng username
**Vị trí:** `backend/app/routers/auth.py`, `backend/app/db/mongo.py`

- Khi register mới kiểm tra trùng email, chưa kiểm tra trùng username.
- Có thể tạo nhiều user cùng username, gây mơ hồ đăng nhập bằng username.

**Khuyến nghị:**
- Thêm check `find_user_by_username` trong endpoint register.
- Tạo unique index cho cả `email` và `username` ở MongoDB.

---

### 3) [High] Endpoint transfer dùng dict thô, dễ phát sinh 500
**Vị trí:** `backend/app/routers/transactions.py`

- `transfer_between_wallets` nhận `payload: dict` và ép `float(payload.get("amount", 0))`.
- Input không hợp lệ (vd amount là chuỗi sai định dạng) có thể gây `ValueError` và trả 500 thay vì 4xx có kiểm soát.

**Khuyến nghị:**
- Dùng Pydantic schema riêng cho transfer (source_wallet_id, dest_wallet_id, amount, note, date).
- Trả lỗi validation chuẩn 422/400 với message rõ ràng.

---

### 4) [Medium] Frontend chưa tận dụng refresh token tự động
**Vị trí:** `frontend/src/services/api.js`

- Khi nhận 401, client logout ngay dù đã lưu `refresh_token`.
- Trải nghiệm người dùng kém khi access token hết hạn (bị đá khỏi phiên).

**Khuyến nghị:**
- Thêm flow refresh token trong response interceptor:
  1. Gọi `/auth/refresh-token` bằng `refresh_token`.
  2. Cập nhật access token mới.
  3. Retry request ban đầu một lần.
  4. Chỉ logout nếu refresh thất bại.

---

### 5) [Medium] Force logout chưa xóa access token trong localStorage
**Vị trí:** `frontend/src/App.jsx`

- Event `auth:logout` hiện chỉ xóa `refresh_token`, chưa xóa `token`.
- Có thể gây trạng thái không nhất quán sau khi reload trang.

**Khuyến nghị:**
- Xóa cả `token` và `refresh_token` trong handler `auth:logout`.

---

### 6) [Medium] Refresh token đang lưu dạng plaintext
**Vị trí:** `backend/app/db/mongo.py`

- Token refresh lưu trực tiếp trong DB (`token` raw string).
- Nếu rò rỉ DB, attacker có thể dùng lại token còn hạn.

**Khuyến nghị:**
- Lưu hash của refresh token (ví dụ SHA-256 + so khớp hash).
- Cân nhắc lưu thêm metadata (user-agent, ip, device) để quản lý phiên tốt hơn.

---

### 7) [Low] `safeGet` nuốt lỗi làm khó quan sát sự cố
**Vị trí:** `frontend/src/pages/DashboardPage.jsx`

- Hàm `safeGet` trả fallback ngay khi lỗi và không log/không hiển thị cảnh báo.
- Có thể khiến dữ liệu hiển thị thiếu nhưng người dùng không biết nguyên nhân.

**Khuyến nghị:**
- Log chi tiết lỗi cho dev (console hoặc telemetry).
- Hiển thị cảnh báo mức nhẹ theo module bị lỗi.

---

### 8) [Low] Lookup tên ví trong Overview có thể tối ưu
**Vị trí:** `frontend/src/components/dashboard/OverviewTab.jsx`

- Mỗi dòng giao dịch gọi `wallets.find(...)` gây lookup lặp.

**Khuyến nghị:**
- Tạo map `walletById` bằng `useMemo` từ component cha và truyền xuống để render nhanh hơn.

## Kết luận
Codebase đã có tiến bộ rõ rệt về tổ chức giao diện và độ đầy đủ nghiệp vụ. Các vấn đề quan trọng nhất hiện tại nằm ở **bảo mật auth** và **độ chặt validation backend**. Ưu tiên xử lý theo thứ tự: (1) secret key + unique username, (2) schema hóa transfer, (3) refresh token flow ở frontend.

## Đề xuất checklist triển khai nhanh
1. Chặn startup nếu `SECRET_KEY` yếu/mặc định.
2. Thêm check trùng username + unique index Mongo.
3. Tạo schema `TransferRequest` và thay payload dict.
4. Bổ sung interceptor refresh token + retry 1 lần.
5. Sửa force logout để xóa cả 2 token.
6. Chuyển refresh token sang cơ chế lưu hash.
