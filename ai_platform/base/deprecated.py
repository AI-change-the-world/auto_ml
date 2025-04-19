# deprecated.py

import functools
import warnings

# 默认显示 DeprecationWarning（你也可以放在你程序入口）
warnings.simplefilter("always", DeprecationWarning)


# deprecated.py

import functools
import inspect
import warnings

warnings.simplefilter("always", DeprecationWarning)


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
