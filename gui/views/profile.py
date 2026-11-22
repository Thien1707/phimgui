import customtkinter as ctk

from gui import api_client


class ProfileFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, user: dict, on_updated):
        super().__init__(master)
        self.user = user
        self.on_updated = on_updated

        ctk.CTkLabel(self, text="Hồ sơ", font=ctk.CTkFont(size=20, weight="bold")).pack(
            anchor="w", padx=12, pady=12
        )
        vip = "VIP" if user.get("isVip") else "Thường"
        if user.get("isAdmin"):
            vip += " · Admin"
        ctk.CTkLabel(self, text=f"Gói: {vip}", text_color="#94a3b8").pack(anchor="w", padx=12)

        self.email = ctk.CTkEntry(self, width=360, placeholder_text="Email")
        self.email.insert(0, user.get("email") or "")
        self.email.pack(padx=12, pady=6)
        self.display = ctk.CTkEntry(self, width=360, placeholder_text="Tên hiển thị")
        self.display.insert(0, user.get("displayName") or "")
        self.display.pack(padx=12, pady=6)
        self.phone = ctk.CTkEntry(self, width=360, placeholder_text="Số điện thoại")
        self.phone.insert(0, user.get("phoneNumber") or "")
        self.phone.pack(padx=12, pady=6)
        self.password = ctk.CTkEntry(self, width=360, placeholder_text="Mật khẩu mới (để trống nếu giữ)", show="*")
        self.password.pack(padx=12, pady=6)

        self.msg = ctk.CTkLabel(self, text="")
        self.msg.pack(padx=12, pady=4)
        ctk.CTkButton(self, text="Lưu thay đổi", command=self._save).pack(padx=12, pady=8, anchor="w")

        if not user.get("isVip"):
            ctk.CTkButton(self, text="Mua VIP (VNPay)", command=self._vip).pack(padx=12, pady=4, anchor="w")

    def _save(self):
        body = {
            "email": self.email.get().strip(),
            "displayName": self.display.get().strip(),
            "phoneNumber": self.phone.get().strip(),
        }
        if self.password.get():
            body["password"] = self.password.get()
        try:
            updated = api_client.api("PUT", "/api/auth/me", json_body=body)
            self.msg.configure(text="Đã lưu.", text_color="#4ade80")
            self.on_updated(updated)
        except api_client.ApiError as e:
            self.msg.configure(text=str(e), text_color="#f87171")

    def _vip(self):
        import webbrowser

        try:
            data = api_client.api("POST", "/api/payment/vnpay-create")
            webbrowser.open(data["payUrl"])
            self.msg.configure(text=f"Đang mở VNPay — mã: {data.get('txnRef')}", text_color="#94a3b8")
        except api_client.ApiError as e:
            self.msg.configure(text=str(e), text_color="#f87171")
