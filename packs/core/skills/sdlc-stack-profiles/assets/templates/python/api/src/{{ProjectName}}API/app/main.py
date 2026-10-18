from app.application import Application

_app_instance = None


def get_app():
    global _app_instance
    if _app_instance is None:
        _app_instance = Application()
    return _app_instance.app


app = get_app()
