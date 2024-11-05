import uvicorn


def start():
    uvicorn.run("main.app:app", host="0.0.0.0", port=80, reload=True)


if __name__ == "__main__":
    start()
