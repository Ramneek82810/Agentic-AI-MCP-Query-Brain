from fastapi import FastAPI

class FastMCP(FastAPI):
    def __init__(self, *args, middleware=None, **kwargs):
        super().__init__(*args, **kwargs)

        if middleware:
            for m in middleware:
                self.add_middleware(m["middleware_class"], **m["options"])

    def tool(self, path: str = None, **kwargs):
        def decorator(func):
            route_path = path or f"/{func.__name__}"
            self.post(route_path, **kwargs)(func)
            return func
        return decorator

app = FastMCP()