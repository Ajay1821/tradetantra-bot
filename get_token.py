
import configparser, webbrowser, requests, urllib.parse, sys, json, os
# Quick script: python get_token.py API_KEY API_SECRET
if len(sys.argv) < 3:
    print("Usage: python get_token.py <API_KEY> <API_SECRET>")
    sys.exit(1)
api_key = sys.argv[1]
secret = sys.argv[2]
redirect = "http://127.0.0.1"
url = f"https://api.upstox.com/v2/login/authorization/dialog?client_id={api_key}&redirect_uri={urllib.parse.quote(redirect)}&response_type=code"
print("Open the following URL in browser and login:
", url)
webbrowser.open(url)
code = input("Paste the 'code=' value from browser redirect URL: ").strip()
r = requests.post("https://api.upstox.com/v2/login/authorization/token",
                  data={"code": code, "client_id": api_key, "client_secret": secret,
                        "redirect_uri": redirect, "grant_type": "authorization_code"})
print("Access token:", r.json().get("data", {}).get("access_token"))
