import os
import requests
import hashlib
import shutil
import time
from pathlib import Path


class DBUpdater:
    def __init__(self):
        self .data_filename = os .getenv(
            'DATA_FILENAME', './data/geoip/networks.csv')
        self .csv_url = os .getenv(
            'CSV_DOWNLOAD_URL',
            'https://ip.guide/bulk/networks.csv')
        self .temp_filename = self .data_filename + ".tmp"
        self .old_filename = self .data_filename + ".old"
        self .cache_dir = Path(self .data_filename).parent

    def _calculate_md5(self, filepath):
        hash_md5 = hashlib .md5()
        with open(filepath, "rb")as f:
            for chunk in iter(lambda: f .read(4096), b""):
                hash_md5 .update(chunk)
        return hash_md5 .hexdigest()

    def _download_file(self):
        print(f"[WARNING] Scaricando il nuovo CSV da: {self .csv_url}")
        try:
            with requests .get(self .csv_url, stream=True, timeout=30)as r:
                r .raise_for_status()
                total_size = int(r .headers .get('content-length', 0))
                downloaded_size = 0
                start_time = time .time()
                with open(self .temp_filename, 'wb')as f:
                    for chunk in r .iter_content(chunk_size=8192):
                        f .write(chunk)
                        downloaded_size += len(chunk)
                        if time .time()-start_time > 1:
                            if total_size > 0:
                                progress = (downloaded_size / total_size)*100
                                print(f"\r[WARNING] Scaricamento: {downloaded_size /
                                                                   (1024 *
                                                                    1024):.2f}MB / {total_size /
                                                                                    (1024 *
                                                                                     1024):.2f}MB ({progress:.1f}%)", end='')
                            else:
                                print(
                                    f"\rScaricamento: {downloaded_size / (1024 * 1024):.2f}MB", end='')
                            start_time = time .time()
                print("\n[INFO] Scaricamento completato.")
            return True
        except requests .exceptions .RequestException as e:
            print(f"[ERROR] Errore durante il download del CSV: {e}")
            if os .path .exists(self .temp_filename):
                os .remove(self .temp_filename)
            return False

    def _validate_csv(self):
        print("[WARNING] Validazione file CSV...")
        try:
            with open(self .temp_filename, 'r', encoding='utf-8')as f:
                header = f .readline()
                if not all(
                    col in header for col in [
                        'network',
                        'asn',
                        'organization',
                        'country']):
                    print(
                        "[ERROR] Errore: Intestazione CSV non valida o colonne mancanti.")
                    return False
                first_data_line = f .readline()
                if not first_data_line .strip():
                    print(
                        "[WARNING] Avviso: Il file CSV sembra vuoto dopo l'intestazione.")
            print("[INFO] Validazione CSV di base superata.")
            return True
        except Exception as e:
            print(f"[ERROR] Errore durante la validazione CSV: {e}")
            return False

    def _update_files(self):
        print("[WARNING] Aggiornamento file CSV...")
        try:
            if os .path .exists(self .data_filename):
                old_md5 = self ._calculate_md5(self .data_filename)
                new_md5 = self ._calculate_md5(self .temp_filename)
                if old_md5 == new_md5:
                    print(
                        "[INFO] Il nuovo CSV è identico a quello esistente. Nessun aggiornamento necessario.")
                    os .remove(self .temp_filename)
                    return True
                if os .path .exists(self .old_filename):
                    os .remove(self .old_filename)
                os .rename(self .data_filename, self .old_filename)
                print(
                    f"   Rinominato '{
                        self .data_filename}' in '{
                        self .old_filename}'")
            shutil .move(self .temp_filename, self .data_filename)
            print(
                f"   Spostato '{
                    self .temp_filename}' a '{
                    self .data_filename}'")
            print("[INFO] CSV aggiornato con successo.")
            self ._clear_cache()
            return True
        except Exception as e:
            print(f"[ERROR] Errore durante l'aggiornamento dei file: {e}")
            return False

    def _clear_cache(self):
        print("[WARNING] Cancellazione file di cache...")
        try:
            cache_files = list(self .cache_dir .glob(
                f"{Path(self .data_filename).stem}_daemon_v*.cache"))
            if not cache_files:
                print("   Nessun file di cache trovato da cancellare.")
                return
            for cache_file in cache_files:
                os .remove(cache_file)
                print(f"   Rimosso: {cache_file}")
            print("[INFO] Cache cancellata.")
        except Exception as e:
            print(f"[ERROR] Errore durante la cancellazione della cache: {e}")

    def update_database(self):
        print("\n=== Avvio Aggiornamento Database CSV ===")
        db_directory = Path(self .data_filename).parent
        if not db_directory .exists():
            print(f"[INFO] Creazione directory: {db_directory}")
            db_directory .mkdir(parents=True, exist_ok=True)
        if not self ._download_file():
            print("[ERROR] Aggiornamento fallito: Impossibile scaricare il file CSV.")
            return False
        if not self ._validate_csv():
            print("[ERROR] Aggiornamento fallito: Validazione CSV fallita.")
            os .remove(self .temp_filename)
            return False
        if not self ._update_files():
            print(
                "[ERROR] Aggiornamento fallito: Errore durante la sostituzione dei file.")
            return False
        print("=== Aggiornamento Database CSV Completato ===")
        return True


if __name__ == '__main__':
    updater = DBUpdater()
    updater .update_database()
