import time
import re
import libs.crypto as crypto
import multiprocessing
import logging

def is_match(match, address):
    return bool(re.match(match, address))

def generate_passphrase(salt, entropy, mnemo):
    return mnemo.generate(strength=entropy) + salt

def worker(match, salt, entropy, lang_dict, Mnemonic, result_queue, stop_event, worker_id=0, stats_dict=None, stats_update_interval=0.5):
    """
    Функция-воркер для генерации адресов в отдельном процессе.
    Результат кладёт в result_queue при нахождении совпадения.
    Обновляет stats_dict[worker_id] количеством попыток для мониторинга скорости.
    """
    mnemo = Mnemonic(lang_dict)
    n = 0
    start_time = time.time()
    last_stats_update = start_time

    while not stop_event.is_set():
        passphrase = generate_passphrase(salt, entropy, mnemo)
        address = crypto.get_account_address(passphrase)
        n += 1

        now = time.time()
        # Обновляем статистику для мониторинга скорости
        if stats_dict is not None and now - last_stats_update >= stats_update_interval:
            stats_dict[worker_id] = (n, now)
            last_stats_update = now

        if is_match(match, address):
            stop_event.set()
            total_time = time.time() - start_time
            if stats_dict is not None:
                stats_dict[worker_id] = (n, time.time())
            print(f"\n[Worker {worker_id}] Найден адрес после {n} попыток за {total_time:.2f} сек. Средняя скорость: {n/total_time:.2f} адресов/сек")
            result_queue.put({
                'passphrase': passphrase,
                'address': address,
                'attempts': n,
                'worker_id': worker_id,
                'total_time': total_time
            })
            break

def generate_wallet(match, salt, entropy, lang_dict, quit_event, Mnemonic, stats_update_interval=0.5, num_processes=None):
    """
    Генерирует кошелек, используя несколько процессов для ускорения поиска.
    """
    if num_processes is None:
        num_processes = multiprocessing.cpu_count()
    
    # Создаем общие объекты для межпроцессного взаимодействия
    result_queue = multiprocessing.Queue()
    stop_event = multiprocessing.Event()
    manager = multiprocessing.Manager()
    stats_dict = manager.dict()
    
    # Запускаем воркеры
    processes = []
    for i in range(num_processes):
        p = multiprocessing.Process(
            target=worker,
            args=(match, salt, entropy, lang_dict, Mnemonic, result_queue, stop_event, i, stats_dict, stats_update_interval)
        )
        p.start()
        processes.append(p)
    
    # Ожидаем результат или прерывание
    result = None
    try:
        while not quit_event.is_set() and not stop_event.is_set():
            if not result_queue.empty():
                result = result_queue.get()
                stop_event.set()
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nПрерывание пользователем")
        stop_event.set()
    
    # Завершаем все процессы
    for p in processes:
        p.join()
    
    # Возвращаем результат, если он был найден
    if result:
        return {
            'passphrase': result['passphrase'],
            'address': result['address'],
        }
    return None
