from fastapi import FastAPI

from app.features.users.routes import router as users_router
from app.features.ussd.routes import router as ussd_router
from app.features.recommendations.routes import router as recommendations_router
from app.features.policies.routes import router as policies_router
from app.features.payments.routes import router as payments_router
from app.features.claims.routes import router as claims_router
from app.features.notifications.routes import router as notifications_router

app = FastAPI(title="SokoSure")

app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(ussd_router)
app.include_router(recommendations_router, prefix="/recommendations", tags=["recommendations"])
app.include_router(policies_router, prefix="/policies", tags=["policies"])
app.include_router(payments_router, prefix="/payments", tags=["payments"])
app.include_router(claims_router, prefix="/claims", tags=["claims"])
app.include_router(notifications_router)

#@app.api_route("/health", methods=["GET", "HEAD"])
#async def health():
#    return {"status": "ok"}