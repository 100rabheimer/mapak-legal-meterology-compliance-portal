import os
import sys
import time
import webbrowser
import threading
import uvicorn
from dotenv import load_dotenv

# Ensure local directories and UTF-8 console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_dir, ".env"))

sys.path.insert(0, base_dir)

def open_browser(url: str):
    time.sleep(1.5)
    print(f"[*] Launching DoCA Enforcement Officer Portal in browser: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[*] Note: Please open {url} in your browser ({e})")

def main():
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    display_host = "localhost" if host in ["0.0.0.0", "127.0.0.1"] else host
    url = f"http://{display_host}:{port}"

    print("\n" + "="*75)
    print("   GOVERNMENT OF INDIA • MINISTRY OF CONSUMER AFFAIRS")
    print("   DEPARTMENT OF CONSUMER AFFAIRS • LEGAL METROLOGY DIVISION")
    print("   ENFORCEMENT OFFICER DASHBOARD & STATUTORY NOTICE GENERATION PORTAL")
    print("="*75)
    print(f"   [+] Inspection Portal URL:  {url}")
    print(f"   [+] Swagger API Explorer:   {url}/docs")
    print(f"   [+] Legal Knowledge Base:   Connected to Module 1")
    print(f"   [+] Multimodal Vision AI:   Connected to Module 2")
    print("="*75 + "\n")

    threading.Thread(target=open_browser, args=(url,), daemon=True).start()
    uvicorn.run("app.api:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    main()
