from aiohttp import web
from .stream_routes import routes


async def web_server():
    app = web.Application(client_max_size=0)  # no upload size limit
    app.add_routes(routes)
    return app
