# Studium Tracker - KI-gestützter Lernplaner
## Funktionen

- **Modul-Verwaltung** - Erstelle und verwalte deine Studienfächer mit Zielstunden und Prüfungsterminen
- **Lernzeit-Tracking** - Erfasse alle Lernsessions mit Datum, Dauer und Notizen
- **Fortschritts-Visualisierung** - Sehe deinen Lernfortschritt mit Prozentanzeigen und Fortschrittsbalken
- **Statistiken-Dashboard** - Übersicht über gelernte Stunden (heute/diese Woche/diesen Monat)
- **KI-Lernplan Generator** - Google Gemini erstellt personalisierte Lernpläne basierend auf deinem Fortschritt
- **Netzwerk-Zugriff** - Zugriff von allen Geräten im Heimnetzwerk (Laptop, Smartphone, Tablet)
- **Responsive Design** - Funktioniert auf Desktop, Tablet und Smartphone

## Beschreibung

Diese Web-Anwendung hilft dir dabei, dein Studium strukturiert zu organisieren und deine Lernzeit effektiv zu planen. Du kannst alle deine Studienfächer mit individuellen Zielstunden und Prüfungsterminen anlegen und für jedes Fach deine Lernsessions mit Datum, Dauer und Notizen erfassen. Die App visualisiert deinen Fortschritt übersichtlich mit Prozentanzeigen und zeigt dir auf einen Blick, wie viele Stunden du bereits investiert hast und wie viel noch zu tun ist. Das besondere Highlight ist die KI-Integration: Google Gemini analysiert deine aktuellen Fortschritte, berücksichtigt deine Prüfungstermine und erstellt dir einen maßgeschneiderten, realistischen Lernplan für die kommenden Wochen. Durch die Installation auf einem Raspberry Pi läuft die App rund um die Uhr in deinem Heimnetzwerk und du kannst von jedem Gerät - egal ob Laptop, Smartphone oder Tablet - jederzeit auf deine Lerndaten zugreifen und sie verwalten.

**Technologie:** Flask Backend | SQLite Datenbank | Google Gemini KI | Responsive Web-Frontend

---

## Installation auf Raspberry Pi

### Schritt 1: Projekt auf den Raspberry Pi übertragen

**Per SSH verbinden:**
```bash
ssh pi@192.168.1.XX
```
*(Ersetze 192.168.1.XX mit der IP-Adresse deines Raspberry Pi)*

**Projektordner erstellen:**
```bash
mkdir -p ~/studium-tracker
cd ~/studium-tracker
```

**Dateien übertragen (von deinem PC aus):**

**Windows PowerShell:**
```powershell
scp -r c:\Python\Uebungen\RaspberrPI_StudiumTracking\* pi@192.168.1.XX:~/studium-tracker/
```

**Mac/Linux:**
```bash
scp -r /pfad/zum/projekt/* pi@192.168.1.XX:~/studium-tracker/
```

---

### Schritt 2: Python und Dependencies installieren

**System aktualisieren:**
```bash
sudo apt update
sudo apt upgrade -y
```

**Python 3 und notwendige Pakete installieren:**
```bash
sudo apt install python3 python3-pip python3-venv -y
```

**Ins Projektverzeichnis wechseln:**
```bash
cd ~/studium-tracker
```

**Virtuelle Python-Umgebung erstellen:**
```bash
python3 -m venv venv
```

**Virtuelle Umgebung aktivieren:**
```bash
source venv/bin/activate
```

**Python-Dependencies installieren:**
```bash
pip install -r requirements.txt
```

---

### Schritt 3: Umgebungsvariablen konfigurieren

**.env Datei erstellen:**
```bash
cp .env.example .env
nano .env
```

**Folgende Werte ausfüllen:**
```env
GEMINI_API_KEY=dein-echter-api-key-hier
FLASK_ENV=production
SECRET_KEY=raspberry-pi-secret-key-12345
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=2048
```

**Google Gemini API Key erhalten:**
1. Gehe zu [https://aistudio.google.com/app/apikey]
2. Melde dich mit deinem Google-Konto an
3. Klicke auf "Create API Key"
4. Kopiere den generierten Key
5. Füge ihn in die `.env` Datei ein

**Speichern und beenden:**
---

### Schritt 4: App testen

**App manuell starten:**
```bash
python3 app.py
```

**Im Browser öffnen:**
```
http://192.168.1.XX:5000
```
*(Ersetze 192.168.1.XX mit der IP deines Raspberry Pi)*

**Wenn alles funktioniert:**
- Du siehst das Dashboard
- Du kannst Module erstellen
- Du kannst Lernsessions erfassen
---

### Schritt 6: Von allen Geräten zugreifen

Die App ist jetzt von jedem Gerät in deinem Heimnetzwerk erreichbar:

**Zugriff über:**
- **Laptop/PC:** `http://192.168.1.XX:5000`
- **Smartphone:** `http://192.168.1.XX:5000`
- **Tablet:** `http://192.168.1.XX:5000`

*(Ersetze 192.168.1.XX mit der IP deines Raspberry Pi)*

**IP-Adresse des Raspberry Pi herausfinden:**
```bash
hostname -I
```
**Tipp:** Gib deinem Raspberry Pi in deinem Router eine feste IP-Adresse, damit sich die Adresse nicht ändert!
---

## Installation abgeschlossen!

Die App läuft jetzt auf deinem Raspberry Pi und startet automatisch beim Booten.

**Nächste Schritte:**
1. Öffne die App in deinem Browser: `http://raspberry-pi-ip:5000`
2. Erstelle dein erstes Modul (z.B. "Programmierung I")
3. Erfasse deine erste Lernsession
4. Generiere deinen persönlichen KI-Lernplan

**Viel Erfolg beim Lernen!**
#

