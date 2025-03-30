# Gemini Facebook Chatbot  

- Tạo bot trả lời tin nhắn tự động với Gemini AI. Tự động phản hồi tin nhắn Messenger bằng Google Generative AI (Gemini).

---

## Cách hoạt động

- Tự động hóa bằng Selenium mà không có API.
- Hỗ trợ giao diện Facebook vào ngày *26/04/2025*: [Xem giao diện Facebook được hỗ trợ](https://vincentng295.github.io/gemini_fbchat/static_page/static_page_www_facebook_com_messages_e2ee_t_9256043717836796.html)
- Hỗ trợ cuộc trò chuyện được mã hóa đầu cuối (E2EE chat)

---

## ⚙️ Cách sử dụng và Thiết lập

- Bạn chỉ cần tạo một repo trống với file [.github/workflows/aichat-schedule.yml](.github/workflows/aichat-schedule.yml) nếu chỉ chạy github workflows
- Vào **Settings** > **Actions** > **General**, ở mục ***Workflow permissions*** chọn *Read and write permissions*
- Xem chi tiết [tại đây](https://vincentng295.github.io/gemini_fbchat/)

### Secrets

Để chạy workflows `aichat-schedule` và `traodoisub`, bạn cần thiết lập các secrets sau:  

- **`PASSWORD`**: Mật khẩu để giải mã các tệp zip trong thư mục `secrets`.
- **`GENKEY`**: [Google Developer API key](https://aistudio.google.com/app/apikey) để sử dụng Gemini API

---

### Github workflows

- Chạy workflow `Run AI Chat on Messenger Account` để đăng nhập Facebook và sao lưu cookies vào nhánh `caches/schedule` cho lần đầu tiên
- Cookies và các file liên quan đã được mã hóa bằng mật khẩu của bạn (`PASSWORD` secret) để không ai có thể truy cập tài khoản Facebook của bạn thông qua việc sử dụng cookies.
- Khi thay đổi tài khoản Facebook, hãy xóa nhánh `cache/schedule` rồi chạy lại workflow `Run AI Chat on Messenger Account`

***[Xem thêm](docs/aichat-schedule.md)***

