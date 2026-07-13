# Scribbleso

Desktopowa aplikacja do przygotowywania tekstu zgloszenia, anonimizacji danych oraz kopiowania albo dopisywania wyniku do plikow `.txt` i `.docx`.

## Uruchomienie z kodu

```powershell
pip install -r requirements.txt
python Scribbleso.py
```

## Build do exe

```powershell
pyinstaller --noconfirm --clean Scribbleso.spec
```

Gotowy plik pojawi sie w katalogu `dist/`.
