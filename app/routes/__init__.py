from app.routes.auth import router as auth_router
from app.routes.dashboard import router as dashboard_router
from app.routes.transactions import router as transactions_router
from app.routes.users import router as users_router

__all__ = ["auth_router", "dashboard_router", "transactions_router", "users_router"]
