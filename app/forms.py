from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SubmitField, TextAreaField, PasswordField # 根据需要导入
from wtforms.validators import DataRequired, URL, NumberRange, Length, Optional, Email # 根据需要导入验证器

class AddTargetForm(FlaskForm):
    """
    用于添加新的监控目标的表单。
    """
    name = StringField(
        '监控名称', 
        validators=[
            DataRequired(message="请输入监控目标的名称。"),
            Length(min=1, max=100, message="名称长度应在1到100个字符之间。")
        ],
        render_kw={"placeholder": "例如：我的博客"}
    )
    url = StringField(
        '监控URL', 
        validators=[
            DataRequired(message="请输入有效的URL。"), 
            URL(message="请输入有效的URL，例如：http://example.com 或 https://example.com")
        ],
        render_kw={"placeholder": "例如：https://www.google.com"}
    )
    check_interval_seconds = IntegerField(
        '检查间隔 (秒)', 
        default=300, 
        validators=[
            DataRequired(message="请输入检查间隔。"), 
            NumberRange(min=30, max=86400, message="检查间隔必须在30秒到86400秒 (24小时) 之间。") # 常见范围
        ],
        render_kw={"min": "30", "max": "86400"}
    )
    is_active = BooleanField('立即激活监控', default=True)
    submit = SubmitField('添加监控目标')

class EditTargetForm(FlaskForm):
    """
    用于编辑现有监控目标的表单。
    与AddTargetForm类似，但可能在验证或字段上略有不同，或者用于不同的路由。
    """
    name = StringField(
        '监控名称', 
        validators=[
            DataRequired(message="请输入监控目标的名称。"),
            Length(min=1, max=100, message="名称长度应在1到100个字符之间。")
        ]
    )
    # URL 通常在编辑时不修改，或者有特殊处理，这里我们允许修改
    url = StringField(
        '监控URL', 
        validators=[
            DataRequired(message="请输入有效的URL。"), 
            URL(message="请输入有效的URL。")
        ]
    )
    check_interval_seconds = IntegerField(
        '检查间隔 (秒)', 
        validators=[
            DataRequired(message="请输入检查间隔。"), 
            NumberRange(min=30, max=86400, message="检查间隔必须在30秒到86400秒之间。")
        ]
    )
    is_active = BooleanField('激活监控')
    submit = SubmitField('更新监控目标')

# 如果将来需要用户登录，可以添加登录表单：
# class LoginForm(FlaskForm):
#     username = StringField('用户名', validators=[DataRequired()])
#     password = PasswordField('密码', validators=[DataRequired()])
#     remember_me = BooleanField('记住我')
#     submit = SubmitField('登录')

# class RegistrationForm(FlaskForm):
#     username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=64)])
#     email = StringField('邮箱', validators=[DataRequired(), Email(), Length(max=120)])
#     password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
#     password2 = PasswordField(
#         '确认密码', validators=[DataRequired(), EqualTo('password', message='两次输入的密码必须一致。')])
#     submit = SubmitField('注册')
