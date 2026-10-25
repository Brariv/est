# est
   
   export SMTP_USER="tucuenta@gmail.com"
   export SMTP_PASS="la contraseña de aplicación"
   python3 iphone_duo_watcher.py --zip "Miami Beach, FL" --parts MK1F4LL/A --to tucuenta@gmail.com
   curl -s "https://www.apple.com/shop/fulfillment-messages?fae=true&pl=true&mts.0=regular&cppart=UNLOCKED/US&parts.0=MK1F4LL/A&location=Miami%20Beach,%20FL" -H "user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/154.0.0.0 Safari/537.36" -H "referer: https://www.apple.com/shop/buy-iphone/iphone-duo" | head -c 600
   caffeinate -i python3 iphone_duo_watcher.py --zip "Miami Beach, FL" --parts MK1F4LL/A --to tucuenta@gmail.com