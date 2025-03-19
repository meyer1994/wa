import uvicorn

from wa.app import create

app = create()

if __name__ == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
