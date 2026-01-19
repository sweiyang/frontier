import argparse
import conduit.sdk as conduit

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the Conduit server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to (default: 8000)")
    args = parser.parse_args()
    
    conduit.serve(host=args.host, port=args.port)