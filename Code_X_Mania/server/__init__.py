from aiohttp import web
from Code_X_Mania.server.stream_routes import routes


async def web_server():
    app = web.Application(client_max_size=0)
    app.add_routes(routes)
    return app
