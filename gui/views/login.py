import customtkinter as ctk

from gui import api_client


class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success

        ctk.CTkLabel(self, text="PHIMHAY-GUI", font=ctk.CTkFont(size=28, weight="bold")).pack(
            pady=(40, 8)
        )
        ctk.CTkLabel(self, text="Đăng nhập").pack(pady=(0, 24))

        self.identifier = ctk.CTkEntry(self, placeholder_text="Email hoặc tên đăng nhập", width=320)
        self.identifier.pack(pady=6)
        self.password = ctk.CTkEntry(self, placeholder_text="Mật khẩu", show="*", width=320)
        self.password.pack(pady=6)

        self.msg = ctk.CTkLabel(self, text="", text_color="#f87171")
        self.msg.pack(pady=8)

        ctk.CTkButton(self, text="Đăng nhập", width=320, command=self._login).pack(pady=8)
        ctk.CTkButton(self, text="Đăng ký", width=320, fg_color="transparent", command=self._signup).pack(
            pady=4
        )

    def _login(self):
        self.msg.configure(text="")
        try:
            data = api_client.api(
                "POST",
                "/api/auth/login",
                json_body={
                    "identifier": self.identifier.get().strip(),
                    "password": self.password.get(),
                },
                token=None,
            )
            api_client.set_token(data["token"])
            self.on_success(data.get("user"))
        except api_client.ApiError as e:
            self.msg.configure(text=str(e))

    def _signup(self):
        self.msg.configure(text="")
        ident = self.identifier.get().strip()
        if "@" not in ident:
            self.msg.configure(text="Đăng ký: nhập email vào ô đầu, mật khẩu bên dưới.")
            return
        display = ident.split("@")[0][:20] or "user"
        try:
            data = api_client.api(
                "POST",
                "/api/auth/register",
                json_body={"email": ident, "password": self.password.get(), "displayName": display},
                token=None,
            )
            api_client.set_token(data["token"])
            self.on_success(data.get("user"))
        except api_client.ApiError as e:
            self.msg.configure(text=str(e))
