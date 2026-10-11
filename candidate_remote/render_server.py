"""Isolated synthetic JARVIS probe web server. NOT a production worker."""
import os
from http.server import ThreadingHTTPServer
from api.probe import handler

def main():
    port=int(os.environ.get("PORT","10000"))
    server=ThreadingHTTPServer(("0.0.0.0",port),handler)
    print(f"JARVIS synthetic preview serving port {port}",flush=True)
    server.serve_forever()

if __name__=="__main__":
    main()
