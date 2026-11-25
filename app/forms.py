from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, Regexp


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Mật khẩu", validators=[DataRequired(), Length(min=8, max=128)])
    username = StringField("Tên đăng nhập", validators=[DataRequired(), Length(min=3, max=80)])
    confirm = PasswordField("Nhập lại mật khẩu", validators=[DataRequired(), EqualTo("password")])
    admin_secret = PasswordField("Admin secret (chỉ khi được cấp)", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Tạo tài khoản")


class LoginForm(FlaskForm):
    identifier = StringField("Tên đăng nhập hoặc Email", validators=[DataRequired(), Length(max=255)])
    password = PasswordField("Mật khẩu", validators=[DataRequired()])
    submit = SubmitField("Đăng nhập")


class MovieForm(FlaskForm):
    slug = StringField("Slug phim", validators=[DataRequired(), Length(max=255)])
    title = StringField("Tên phim", validators=[DataRequired(), Length(max=255)])
    origin_name = StringField("Tên gốc", validators=[Optional(), Length(max=255)])
    year = IntegerField("Năm", validators=[Optional(), NumberRange(min=1888, max=2100)])
    category = StringField("Thể loại", validators=[Optional(), Length(max=100)])
    poster_url = StringField("URL poster", validators=[Optional(), Length(max=2000)])
    description = TextAreaField("Mô tả", validators=[Optional(), Length(max=10000)])
    is_vip = BooleanField("Chỉ dành cho VIP")
    submit = SubmitField("Lưu phim")


class MovieSlugForm(FlaskForm):
    slug = StringField(
        "Slug phimapi",
        validators=[DataRequired(), Length(max=255), Regexp(r"^[a-zA-Z0-9_-]+$")],
    )
    submit = SubmitField("Tải thông tin phim")


class SearchForm(FlaskForm):
    q = StringField("Tìm tên phim", validators=[Optional(), Length(max=120)])


class CommentForm(FlaskForm):
    body = TextAreaField("Bình luận", validators=[DataRequired(), Length(min=1, max=1500)])
    submit = SubmitField("Gửi bình luận")
