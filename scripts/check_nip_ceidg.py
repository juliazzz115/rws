"""
Скрипт для автоматичної перевірки дат початку діяльності по NIP через CEIDG API
"""
import requests
import json
import time
import csv
from datetime import datetime

def check_nip_in_ceidg(nip):
    """
    Перевіряє NIP через публічний API CEIDG
    Повертає дату початку діяльності
    """
    try:
        # API CEIDG - публічний доступ
        url = f"https://dane.biznes.gov.pl/api/ceidg/v2/firma/{nip}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()

            # Шукаємо дату початку діяльності
            if 'firma' in data and len(data['firma']) > 0:
                firma = data['firma'][0]

                # Дата початку діяльності
                data_rozpoczecia = firma.get('dataRozpoczecia', None)

                # Назва фірми
                nazwa = firma.get('nazwa', '')

                # Статус (aktywna, zawieszona, etc.)
                status = firma.get('statusDzialalnosci', '')

                return {
                    'nip': nip,
                    'nazwa': nazwa,
                    'data_rozpoczecia': data_rozpoczecia,
                    'status': status,
                    'found': True
                }
            else:
                return {
                    'nip': nip,
                    'found': False,
                    'error': 'Nie znaleziono firmy'
                }
        else:
            return {
                'nip': nip,
                'found': False,
                'error': f'HTTP {response.status_code}'
            }

    except Exception as e:
        return {
            'nip': nip,
            'found': False,
            'error': str(e)
        }

def process_csv(input_file, output_file):
    """
    Przetwarza plik CSV z NIP-ami i zapisuje wyniki
    """
    results = []

    # Czytaj plik wejściowy
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        clients = list(reader)

    print(f"Znaleziono {len(clients)} klientów do sprawdzenia")

    # Sprawdź każdy NIP
    for i, client in enumerate(clients, 1):
        nip = client['NIP'].strip()
        nazwa_z_pliku = client['Nazwa firmy']

        # Pomiń testowe NIP-y
        if nip in ['1111111111', '0000000009', '0000090099', '0000000333', '0000000000']:
            print(f"{i}/{len(clients)}: Pomijam testowy NIP {nip}")
            continue

        if not (len(nip) == 10 and nip.isdigit()):
            print(f"{i}/{len(clients)}: Nieprawidłowy NIP {nip}")
            continue

        print(f"{i}/{len(clients)}: Sprawdzam NIP {nip} ({nazwa_z_pliku})...")

        result = check_nip_in_ceidg(nip)
        result['nazwa_z_pliku'] = nazwa_z_pliku
        results.append(result)

        # Opóźnienie żeby nie przeciążać API
        time.sleep(2)

        # Zapisuj wyniki co 50 rekordów
        if i % 50 == 0:
            save_results(results, output_file)
            print(f"Zapisano wyniki po {i} rekordach")

    # Zapisz ostateczne wyniki
    save_results(results, output_file)

    return results

def save_results(results, output_file):
    """
    Zapisuje wyniki do pliku CSV
    """
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['nip', 'nazwa_z_pliku', 'nazwa_z_ceidg', 'data_rozpoczecia', 'status', 'found', 'error']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        for r in results:
            writer.writerow({
                'nip': r.get('nip', ''),
                'nazwa_z_pliku': r.get('nazwa_z_pliku', ''),
                'nazwa_z_ceidg': r.get('nazwa', ''),
                'data_rozpoczecia': r.get('data_rozpoczecia', ''),
                'status': r.get('status', ''),
                'found': r.get('found', False),
                'error': r.get('error', '')
            })

if __name__ == "__main__":
    input_file = "clients_individual.csv"  # Ваш вхідний файл
    output_file = f"nip_dates_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    print("="*60)
    print("Скрипт перевірки дат початку діяльності по NIP")
    print("="*60)

    results = process_csv(input_file, output_file)

    # Статистика
    found = sum(1 for r in results if r.get('found', False))
    not_found = len(results) - found

    print("\n" + "="*60)
    print("РЕЗУЛЬТАТИ:")
    print(f"Всього перевірено: {len(results)}")
    print(f"Знайдено в CEIDG: {found}")
    print(f"Не знайдено: {not_found}")
    print(f"Результати збережено в: {output_file}")
    print("="*60)
