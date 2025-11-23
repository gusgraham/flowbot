from fastapi import FastAPI

app = FastAPI(title="FlowBot Hub")

@app.get("/")
def read_root():
    return {"message": "Welcome to FlowBot Hub"}
