import functools
import inspect
import warnings

# 忽略第三方模块中的 DeprecationWarning
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, module=r"^(?!ai_platform).*"
)


def deprecated(reason: str = ""):
    """
    支持函数或类的通用 @deprecated 装饰器
    :param reason: 弃用原因（可选）
    """

    def decorator(obj):
        message = f"{obj.__name__} is deprecated."
        if reason:
            message += f" {reason}"

        if inspect.isclass(obj):
            # 装饰类
            orig_init = obj.__init__

            @functools.wraps(orig_init)
            def new_init(self, *args, **kwargs):
                warnings.warn(message, category=DeprecationWarning, stacklevel=2)
                return orig_init(self, *args, **kwargs)

            obj.__init__ = new_init
            return obj

        elif callable(obj):
            # 装饰函数或方法
            @functools.wraps(obj)
            def wrapper(*args, **kwargs):
                warnings.warn(message, category=DeprecationWarning, stacklevel=2)
                return obj(*args, **kwargs)

            return wrapper

        else:
            raise TypeError("@deprecated can only be used on functions or classes")

    return decorator
