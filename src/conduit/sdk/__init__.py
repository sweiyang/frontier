import uvicorn


def serve(host="0.0.0.0", port=8000):
    """
    Serve the Conduit backend and frontend.
    """
    print(f"Starting Conduit server on {host}:{port}...")
    try:
        uvicorn.run("conduit.api.main:app", host=host, port=port, reload=True)
    except Exception as e:
        print(f"Failed to start server: {e}")
