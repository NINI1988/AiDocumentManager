Du bist ein Experte für Python-Automatisierung und Machine Learning mit scikit-learn. 
Deine Aufgabe ist es, ein lokales Dokumenten-Sortierskript zu erstellen, das meine bestehende OneDrive-Ordnerstruktur nutzt, um neue PDFs automatisch zu klassifizieren und zu verschieben.

ANFORDERUNGEN:
1. TRAINING (Historie nutzen):
   - Das erste Script muss beim Start alle bestehenden PDFs in "G:\scan\test_documents\Dokumente" rekursiv durchsuchen.
   - Der Pfad relativ zur Hauptkategorie (z.B. "Versicherungen/Deutsche Rentenversicherung") dient als Label (Zielklasse).
   - Extrahiere den Textinhalt aller gefundenen PDFs (nutze pdfplumber für Text-PDFs).
   - Trainiere ein Pipeline-Modell aus TfidfVectorizer und MultinomialNB (oder LinearSVC) auf diesen Daten.
   - Speichere das trainierte Modell als "classifier_model.pkl".

2. VORHERSAGE & SORTIERUNG (Live-Betrieb):
   - Ein zweites script Überwacht den Ordner "G:\scan\1. Inbox" mit der Bibliothek 'watchdog'.
   - Bei neuer PDF: Text extrahieren, Modell laden und Vorhersage treffen.
   - WICHTIG: Nutze 'predict_proba', um die Konfidenz der Vorhersage zu prüfen.
     - Wenn Konfidenz > 0.75: Datei automatisch in den vorhergesagten Ordner "G:\scan\3. Review" verschieben und umbenennen (Format: "YYYY.MM.DD Betreff.pdf").
     - Wenn Konfidenz < 0.75: Datei in den Ordner "G:\scan\2. Unsure" verschieben und eine Log-Datei schreiben.

3. SICHERHEIT & ONE DRIVE:
   - Implementiere eine Verzögerung (sleep 2-3 Sek) nach dem Erkennen einer neuen Datei, um sicherzustellen, dass der OneDrive-Sync abgeschlossen ist, bevor gelesen wird.
   - Verhindere Endlosschleifen: Das Skript darf keine Dateien verarbeiten, die es selbst gerade verschoben hat (ignoriere alle Ordner außer "1. Inbox").
   - Erstelle ein detailliertes Logfile ("log.txt"), das jede Aktion, die Konfidenz und eventuelle Fehler festhält.

4. AUSGABE:
   - Schreibe den vollständigen, lauffähigen Python-Code.
   - Erstelle eine requirements.txt   