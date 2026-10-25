#!/usr/bin/env python3
"""
Vigila la disponibilidad de pickup del iPhone Duo en Apple Stores cerca de un ZIP
y te manda un CORREO cuando aparece stock.

Uso:
  export SMTP_USER="tucuenta@gmail.com"
  export SMTP_PASS="xxxx xxxx xxxx xxxx"     # contrasena de aplicacion de Gmail
  python3 iphone_duo_watcher.py --zip 33131 --parts MXXXXLL/A MYYYYLL/A --to tucuenta@gmail.com

Como obtener los part numbers (--parts):
  1. Abre la pagina de compra del iPhone Duo en apple.com/shop/buy-iphone
  2. Elige color y almacenamiento, abre DevTools (F12) > Network
  3. Haz clic en "Check availability" para pickup
  4. Busca la request "fulfillment-messages" y copia el valor de parts.0=...
     (algo como MXXXXLL/A). Repite por cada configuracion que aceptes.

Contrasena de aplicacion de Gmail (necesitas verificacion en 2 pasos activada):
  myaccount.google.com/apppasswords > crea una y pegala en SMTP_PASS.
  Para otro proveedor usa --smtp-host y --smtp-port (por defecto smtp.gmail.com:465).

Tip: para que el correo te suene como alerta en el celular, crea en Gmail un filtro
para el asunto "iPhone Duo DISPONIBLE" y marcalo como importante / con notificacion.

Solo usa la libreria estandar de Python 3.
Nota: es un endpoint interno no documentado; Apple puede cambiarlo. Manten el intervalo >= 60 s.
"""
import argparse
import json
import os
import smtplib
import sys
import time
import urllib.parse
import urllib.request
from email.message import EmailMessage

ENDPOINT = "https://www.apple.com/shop/fulfillment-messages"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en,es-US;q=0.9,es-419;q=0.8,es;q=0.7",
    "Referer": "https://www.apple.com/shop/buy-iphone/iphone-duo",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


def fetch_stores(zip_code: str, parts: list[str]) -> list[dict]:
    params = [("fae", "true"), ("pl", "true"), ("mts.0", "regular"),
              ("cppart", "UNLOCKED/US"), ("location", zip_code)]
    for i, p in enumerate(parts):
        params.append((f"parts.{i}", p))
    url = f"{ENDPOINT}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    return data["body"]["content"]["pickupMessage"]["stores"]


def find_available(stores: list[dict]) -> list[str]:
    hits = []
    for s in stores:
        for part, info in s.get("partsAvailability", {}).items():
            if str(info.get("pickupDisplay", "")).lower() == "available":
                name = info.get("storePickupProductTitle") or part
                hits.append(
                    f"{s.get('storeName')} ({s.get('city')}): {name} "
                    f"- {info.get('pickupSearchQuote', 'Available')}"
                )
    return hits


def send_email(args, body: str) -> None:
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASS"]
    msg = EmailMessage()
    msg["Subject"] = "iPhone Duo DISPONIBLE para pickup"
    msg["From"] = user
    msg["To"] = args.to
    msg.set_content(
        body
        + "\n\nCompralo YA: apple.com/shop/buy-iphone (elige pickup en esa tienda)."
    )
    with smtplib.SMTP_SSL(args.smtp_host, args.smtp_port, timeout=30) as s:
        s.login(user, password)
        s.send_message(msg)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True)
    ap.add_argument("--parts", nargs="+", required=True)
    ap.add_argument("--to", required=True, help="correo donde recibir la alerta")
    ap.add_argument("--smtp-host", default="smtp.gmail.com")
    ap.add_argument("--smtp-port", type=int, default=465)
    ap.add_argument("--interval", type=int, default=60)
    args = ap.parse_args()

    if not (os.environ.get("SMTP_USER") and os.environ.get("SMTP_PASS")):
        sys.exit("Faltan las variables de entorno SMTP_USER y SMTP_PASS (ver encabezado del script).")

    last_alert = set()
    print(f"Vigilando {args.parts} cerca de {args.zip} cada {args.interval}s. Ctrl+C para salir.")
    while True:
        try:
            hits = find_available(fetch_stores(args.zip, args.parts))
            ts = time.strftime("%H:%M:%S")
            if hits:
                print(f"[{ts}] DISPONIBLE:\n  " + "\n  ".join(hits))
                if set(hits) != last_alert:
                    send_email(args, "\n".join(hits))
                    print(f"[{ts}] correo enviado a {args.to}")
                    last_alert = set(hits)
            else:
                print(f"[{ts}] sin stock")
                last_alert = set()
        except Exception as e:  # red caida, bloqueo temporal, formato cambiado, SMTP...
            print(f"[{time.strftime('%H:%M:%S')}] error: {e}", file=sys.stderr)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()