#!/bin/bash

if [ "$EUID" -ne 0 ]; then
    echo "❌ Dieses Script muss als root ausgeführt werden." >&2
    exit 1
fi


echo "📥 Starte Update der Flask-App vom Git-Repository..."

cd /var/www/faktura || exit
git pull origin main

if [ $? -eq 0 ]; then
    echo "✅ Git-Update erfolgreich!"
    echo "🔁 Trigger mod_wsgi-Reload..."
    touch /var/www/faktura/wsgi.py
    echo "🚀 App wurde neu geladen."
else
    echo "❌ Git-Update fehlgeschlagen. Keine Änderungen übernommen."
fi
#1~#!/bin/bash


#echo "📥 Starte Update der Flask-App vom Git-Repository..."

#cd /var/www/faktura || exit
#git pull origin main

#if [ $? -eq 0 ]; then
#    echo "✅ Git-Update erfolgreich!"
#    echo "🔁 Trigger mod_wsgi-Reload..."
#    touch /var/www/faktura/wsgi.py
#    echo "🚀 App wurde neu geladen."
#else
#    echo "❌ Git-Update fehlgeschlagen. Keine Änderungen übernommen."
#fi
