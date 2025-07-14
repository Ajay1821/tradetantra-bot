
# TradeTantra Bot – Render Deployment Guide (Hindi)

## 1. GitHub Repository
1. इस `tradetantra-bot` फोल्डर को GitHub repo में push करें (या web UI से फ़ाइलें अपलोड करें)।

## 2. Render.com पर नया Web Service
1. https://render.com  पर Google/GitHub से लॉग‑इन करें।
2. "New +" → **Web Service** → **Deploy from GitHub** → इस repo को चुनें।
3. Build & Start commands:
   - **Build**: *render default* (requirements.txt ऑटो‑detect हो जायेगा)
   - **Start**: `python main.py`

## 3. Environment Variables
| KEY | VALUE |
|-----|-------|
| TG_TOKEN | Telegram Bot Token |
| TG_CH | @ChannelUsername |
| UP_API_KEY | Upstox API Key |
| UP_API_SECRET | Upstox Secret |
| UP_ACCESS | Daily access token (get_token.py से) |

## 4. रोज़ का Token Refresh
```bash
python get_token.py <API_KEY> <API_SECRET>
```
Browser से login → "code" कॉपी करें → Access‑token मिलेगा।  
Render dashboard → Web Service → Environment → `UP_ACCESS` अपडेट करें → "Save & Deploy".

## 5. Telegram Commands
```
/add SBIN 1050 1020 1100   # Entry, Stoploss, Target
/post कोई भी टेक्स्ट         # Manual post to channel
```

## 6. टाइम बचाने की टिप
Market ख़त्म होने पर Render service "Suspend" कर दें (Usage बचता है)।
सुबह token update के बाद "Resume" दबायें, 10 सेकंड में Bot Live।
