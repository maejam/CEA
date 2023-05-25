from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from user import app as user_app
from document import app as document_app

app = FastAPI()

origins = ["*"]

# Middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the user and document routes
app.mount("/user", user_app)
app.mount("/document", document_app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)