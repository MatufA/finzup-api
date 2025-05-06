import uvicorn
from finzup_api.config import get_settings

settings = get_settings()

if __name__ == "__main__":
    uvicorn.run(
        "finzup_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1
    ) 