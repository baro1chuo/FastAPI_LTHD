# Benchmark Flask, Django REST Framework và FastAPI

Bộ benchmark chạy ba ứng dụng trên cùng máy, cùng JSON đầu vào và cùng số request. Không cần cài công cụ tải ngoài như `hey`; chương trình đo dùng thư viện chuẩn Python và lưu kết quả vào `benchmark_results.csv`.

## 1. Cài đặt

Mở PowerShell tại thư mục dự án:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-bench.txt
```

Nếu đã có `.venv`, có thể bỏ qua lệnh tạo môi trường.

## 2. Khởi động ba server

Mở ba cửa sổ PowerShell riêng, tại thư mục dự án, và để các tiến trình chạy:

```powershell
.\.venv\Scripts\uvicorn.exe bench_fastapi:app --host 127.0.0.1 --port 8000 --workers 1
```

```powershell
.\.venv\Scripts\waitress-serve.exe --listen=127.0.0.1:8001 --threads=50 bench_flask:app
```

```powershell
.\.venv\Scripts\waitress-serve.exe --listen=127.0.0.1:8002 --threads=50 bench_drf:application
```

FastAPI chạy một worker ASGI; Flask và DRF chạy Waitress với 50 luồng. Cấu hình này phù hợp để quan sát khác biệt khi chờ I/O, nhưng không phải phép đo tuyệt đối độc lập với máy chủ ứng dụng. Khi công bố kết quả, cần ghi rõ cấu hình này và phiên bản Python/framework.

## 3. Chạy đo

Trong cửa sổ PowerShell thứ tư:

```powershell
.\.venv\Scripts\python.exe run_bench.py
```

Mặc định, mỗi kịch bản có 50 request khởi động, 500 request đo, concurrency 50 và 3 lần lặp. Bảng kết quả được in ra màn hình và lưu vào `benchmark_results.csv`.

Có thể thay đổi tải đo:

```powershell
.\.venv\Scripts\python.exe run_bench.py --requests 1000 --concurrency 100 --runs 5 --warmup 100
```

Các kịch bản gồm:

- Tạo dữ liệu hợp lệ (`POST /items`).
- Gửi dữ liệu không hợp lệ để đo đường validation. FastAPI/Flask dự kiến trả `422`, còn DRF dự kiến trả `400`; đây là khác biệt mặc định của framework, không phải lỗi benchmark.
- Chờ I/O 100 ms (`/io-async` trên FastAPI; `/io-sync` trên Flask; `/io/` trên DRF).
- Bài C trên FastAPI: so sánh `await asyncio.sleep` (`/io-async`), `time.sleep` trong `async def` (`/io-blocking-wrong`) và `time.sleep` trong `def` (`/io-sync`). Ba dòng này dùng chung số request và concurrency đã cấu hình, nên có thể đối chiếu trực tiếp trong bảng/CSV.

Ví dụ chạy riêng một lượt đo với 25 kết nối đồng thời; runner sẽ chạy các kịch bản A, B và C:

```powershell
.\.venv\Scripts\python.exe run_bench.py --requests 500 --concurrency 25 --runs 3 --output bai-c-c25.csv
```

Bài C chỉ có trên FastAPI. Endpoint `time.sleep` trong `async def` cố ý chặn event loop để minh họa cách dùng async không đúng; không dùng mẫu này trong ứng dụng thực tế.

Thông lượng (RPS) và các số liệu độ trễ là trung vị qua các lần chạy. `p95` là phân vị 95 của từng lần đo; báo cáo lấy trung vị các p95. Mã HTTP và request lỗi cũng được ghi lại để phát hiện server không sẵn sàng hoặc phản hồi không như dự kiến. Nếu có lỗi kết nối hoặc mã trạng thái ngoài dự kiến, chương trình kết thúc với lỗi sau khi lưu CSV.

Để kết quả có ý nghĩa, chạy trên máy không tải tác vụ khác, dùng cùng cấu hình cho mọi lần đo và không so sánh số liệu thu được trên các máy hoặc môi trường khác nhau. Thời gian chạy có thể tăng theo `requests`, `concurrency` và `runs`.
