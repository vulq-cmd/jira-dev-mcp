# Asset đã export / tải về → `~/Downloads`

Khi dev nói đã **export / tải / download** một ảnh hoặc file (vd *"tôi export design rồi"*, *"ảnh tải về rồi"*, *"file trong downloads"*, *"vừa lưu ảnh"*), mặc định nó nằm ở **`~/Downloads`** (`/Users/avada/Downloads`). AI **tự vào đó lấy** — KHÔNG bắt dev kéo-thả hay dán path.

## Cách lấy
1. **Liệt kê file mới nhất** (ưu tiên file vừa tạo trong vài phút — đúng cái dev vừa export):
   - Vừa export (cửa sổ thời gian): `find ~/Downloads -maxdepth 1 -type f -mmin -10 | sort` *(chỉnh `-mmin` theo lúc dev export)*
   - Ảnh mới nhất: `ls -t ~/Downloads/*.{png,jpg,jpeg,webp,gif,svg} 2>/dev/null | head -5`
   - Mọi loại (pdf/zip/mp4…): `ls -t ~/Downloads | head -10`
2. **Khớp tên** nếu dev gợi ý tên ("ảnh banner", "mockup checkout") → lọc thêm theo tên.
3. **Chọn:**
   - 1 file mới rõ ràng → dùng luôn, **báo tên đang dùng**.
   - Nhiều file mới / không chắc → liệt kê 3–5 ứng viên mới nhất (tên + giờ sửa) → **HỎI dev chọn**.
4. **Đọc:**
   - Ảnh (png/jpg/webp/svg…) → **Read path bằng vision**.
   - PDF / doc / video nặng → `ai-multimodal` skill.

## Lưu ý
- **Read-only**: chỉ đọc, KHÔNG xoá/di chuyển file trong `~/Downloads`.
- Dùng **path tuyệt đối** `/Users/avada/Downloads/<file>` khi Read.
- File Figma export thường tên kiểu `<Frame> @2x.png`, `Group 123.png`, `Frame 1.png` → cứ ưu tiên file **mới nhất** sau khi dev nói "vừa export".
- Đây là phương án khi dev **tự export tay**; nếu có URL Figma thì `figma_get_frames` (render) / `figma_get_specs` (spec chính xác) vẫn tiện hơn.
