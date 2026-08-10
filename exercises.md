# Phiếu Phản Ánh — K3 Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: điền câu trả lời trực tiếp dưới mỗi câu hỏi.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Nguyễn Văn Ninh  Mã học viên: 2A202601419

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

> `Settings()` fail-fast khi thiếu `AGENT_API_KEY`, và `lifespan` gọi `get_settings()` ngay đầu startup, trước khi đăng ký signal handler hay ghi log `service_started`; vì vậy một process Railway thiếu secret sẽ dừng trước khi trả `/health` hay nhận traffic. Ví dụ, nếu quên khai báo `AGENT_API_KEY` trong Railway Variables, deploy lỗi ngay khi khởi động thay vì chạy với khóa mặc định `"changeme"` để người khác đoán rồi gọi `/ask` làm phát sinh chi phí. Với Docker Compose, `${AGENT_API_KEY:?AGENT_API_KEY must be set}` còn chặn interpolation trước khi container agent được tạo; hai lớp này bổ sung nhau vì Railway không dùng Compose interpolation.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

> Dòng log JSON thực tế (đã không chứa API key) tôi nhận được sau `POST /ask` là: `{"event": "ask_completed", "level": "info", "timestamp": "2026-08-10T04:24:08.769863+00:00", "user_id": "exercise-log-9f1275aa", "tokens_in": 3, "tokens_out": 41, "cost_usd": 2.505e-05}`.
>
> Từ các field này tôi có thể (1) lọc/đếm riêng event `ask_completed` theo `user_id` hoặc theo thời gian và (2) cộng `cost_usd` hay cảnh báo khi `tokens_out` cao. `print("đã trả lời xong")` không có cấu trúc, user, thời gian, token hoặc chi phí để máy lọc và tổng hợp tin cậy.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | 1.73 GB |
| Multi-stage | 270 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

> Tôi build Dockerfile gốc tại commit `775cc02` thành `agent:single-task8` và Dockerfile hiện tại thành `agent:multi-task8`. Hai số đo quan sát được là khác loại: `docker image inspect .Size` (content của containerd) là 1,446,266,683 byte cho 1-stage và 63,689,823 byte (khoảng 63.69 MB) cho multi-stage; `docker images` hiển thị dung lượng unpacked/snapshot trên disk riêng là 1.73 GB và 270 MB tương ứng. Vì vậy 270 MB không phải làm tròn từ 63.69 MB, và 1.73 GB cũng không phải làm tròn từ 1,446,266,683 byte. Chênh lệch chủ yếu là base `python:3.11` đầy đủ cùng các thứ build/install nằm trong image một stage; multi-stage dùng `python:3.11-slim` ở runtime và chỉ copy `/install`, `app`, `utils`, nên không mang toàn bộ môi trường builder sang image cuối.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

> Trong context tạm, sau khi đổi đúng một ký tự trong comment của `app/main.py`, build ghi `CACHED` cho `WORKDIR /app`, `COPY requirements.txt .`, `RUN pip install --no-cache-dir --prefix=/install -r requirements.txt` và `COPY --from=builder /install /usr/local`. Build lại `COPY app ./app`, `COPY utils ./utils` và `RUN useradd --create-home --uid 10001 appuser` (đều `DONE`, không phải `CACHED`).
>
> Nếu đặt `COPY . .` trước `RUN pip install`, thay đổi trong `app/main.py` sẽ làm invalid layer `COPY . .`; vì `RUN pip install` nằm sau nó, layer cài dependency cũng phải chạy lại dù `requirements.txt` không đổi.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

> Chuỗi rủi ro là: lỗ hổng Python cho phép chạy lệnh trong container → lệnh đó có UID 0 nếu container chạy root → kẻ tấn công khai thác thêm đường thoát container hoặc cấu hình host nguy hiểm (ví dụ Docker socket/mount đặc quyền) để đạt quyền cao trên host. `USER appuser` trong Dockerfile làm code và lệnh sau khai thác bắt đầu bằng UID 10001, nên không có quyền root trong container; nó giảm đặc quyền ban đầu, dù không thay thế việc vá lỗ hổng hay loại bỏ cấu hình host nguy hiểm.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

> Tối đa là 20 request trong 2 giây: gửi 10 request ở 10:00:59 rồi thêm 10 request ở 10:01:01. Bộ đếm theo phút đồng hồ reset khi qua giây 00 nên cả hai nhóm đều dưới hạn mức 10/phút của từng phút; sliding window 60 giây của `RateLimiter` giữ các timestamp gần nhất nên chặn nhóm thứ hai.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

> Rate limit của `RateLimiter` giới hạn số request trong cửa sổ 60 giây theo user; cost guard của `CostGuard` kiểm tra tổng USD theo user/tháng. Ví dụ user đang ở 9.99999 USD: một request còn quota được `guard.check()` cho qua vì mặc định `estimated_cost=0.0`, rồi `record()` cộng chi phí thực tế 0.00002505 USD thành 10.00001505 USD. Request đầu tiên của phút/cửa sổ mới qua rate limit nhưng `spent + 0.0 > 10.0` nên cost guard trả 402 `monthly budget exceeded`; nếu đúng bằng 10.0 thì điều kiện `>` chưa chặn. Chiều ngược lại, user còn dưới 10.0 USD nhưng gửi request thứ 11 trong chưa đầy 60 giây: endpoint thực tế gọi limiter trước nên trả 429 `rate limit exceeded`; cost guard vẫn có đủ ngân sách và sẽ cho qua nếu được gọi.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

> Với source hiện tại, `/health` chỉ kiểm tra process, còn `/ready` gọi `store.ping()`. Nếu gộp và để `/health` kiểm tra Redis, Redis mất đúng 30 giây có thể chồng lên một hoặc hai probe theo `interval: 30s`, tùy pha; vẫn ít hơn `retries: 3`, nên Docker health hiện vẫn là healthy, chỉ tăng failing streak. Theo thứ tự: probe gộp có thể trả 503; `/ready` và các thao tác phụ thuộc Redis thất bại; Redis phục hồi trước ngưỡng ba lỗi; probe kế tiếp thành công. Compose không có `restart:`, health status của Docker tự nó không restart container, và Compose/nginx hiện không dùng `/ready` để tự rút instance khỏi traffic, nên không có restart storm hay tự loại traffic trong cấu hình thực tế này.
>
> Counterfactual riêng: với outage dài hơn và một orchestrator/load balancer được cấu hình dùng liveness/readiness, đưa Redis vào liveness có thể khiến cả ba agent lần lượt bị rút traffic hoặc restart lặp lại dù process còn sống. Giữ `/health` tách riêng thì liveness vẫn sống; `/ready` mới là tín hiệu để một load balancer có hỗ trợ readiness ngừng gửi traffic, rồi nhận lại khi Redis hồi phục.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

> Tôi chạy override tạm có nginx ở host 8000, xóa port host của agent và scale `agent=3`; `docker compose ps` có đúng `day12-completion-agent-1`, `-2`, `-3`. Với cùng user mới `exercise-scale-6c72ae5c`, bốn response qua nginx có `history_length` tăng đơn điệu `0, 2, 4, 6`: mỗi `/ask` đọc lịch sử trước, rồi ghi thêm user và assistant vào Redis List. Nếu dùng dict Python trong RAM, mỗi process có dict riêng; request rơi sang container khác sẽ thường thấy 0 hoặc một chuỗi riêng của container đó, không có một dãy toàn cục 0, 2, 4, 6.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> Lỗi thật khi thử Railway là lệnh `railway whoami` trả đúng: `Unauthorized. Please login with railway login`. Đây là blocker xác thực trước deployment: máy có Railway CLI nhưng chưa có phiên đăng nhập hợp lệ, nên chưa thể tạo/deploy cloud; lỗi cloud vẫn chưa được giải quyết. `railway login` là bước sửa tiếp theo bắt buộc, nhưng tôi chưa thực thi nó nên không khẳng định có deploy Railway thành công. Cách xử lý thực tế đã dùng là Docker Compose local fallback, nơi `/health` và `/ready` đều 200.
