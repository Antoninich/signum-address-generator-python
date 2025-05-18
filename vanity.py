import argparse
import os
import re
import signal
import sys
import logging
import time
from mnemonic import Mnemonic
import multiprocessing as mp

import libs.crypto as crypto
from wallet_generator import worker


WORDS_ENTROPY = {
    '12': 128,
    '15': 160,
    '18': 192,
    '21': 224,
    '24': 256,
}
LANGUAGE_DICT = {
    'en': 'english',
    'fr': 'french',
    'it': 'italian',
    'ja': 'japanese',
    'ko': 'korean',
    'es': 'spanish',
    'tr': 'turkish',
    'cs': 'czech',
    'pt': 'portuguese',
}
MASK = r'^23456789ABCDEFGHJKLMNPQRSTUVWXYZ?#@-+$'
SIGNUM_ADDRESS_MASK = r'S-([2-9A-HJ-NP-Z?#@]{4}-){3}[2-9A-H?#@][2-9A-HJ-NP-Z?#@]{4}'  # noqa: E501
PROCESSES = os.cpu_count()


def Arguments():
    parser = argparse.ArgumentParser(
        description='Signum Vanity Address Generator'
    )

    parser.add_argument(
        '-m', '--match',
        help="""Specify the rules for the desired address.
        It must be at least one char long.
        No 0, O, I or 1 are allowed.
        Following wildcars can be used:
        '?' - Matches any char
        '@' - Matches only letters [A-Z]
        '#' - Matches only numbers [2-9]
        '-' - Use to organize the mask, does not affect result.
        Default: S-????-????-????-?????""",
        required=False,
        nargs='?',
        const='12',
        default='S-????-????-????-?????',
        type=str
    )
    parser.add_argument(
        '-s', '--salt',
        help=('Add your salt to the bip39 word list'),
        required=False,
        default='',
        type=str
    )
    parser.add_argument(
        '-l', '--lenght',
        help=(
            f"Mnemonic lenght {(', ').join(WORDS_ENTROPY.keys())}. "
            "Default: 12"
        ),
        choices=WORDS_ENTROPY.keys(),
        required=False,
        nargs='?',
        default='12',
        const='12',
        type=str
    )
    parser.add_argument(
        '-d', '--dict',
        help=(
            """Dictionary language for bip-39.
            en - english, fr - french, it - italian, ja - japanese,
            ko - korean, es - spanish, tr - turkish, cs - czech,
            pt - portuguese.
            Default is english"""
        ),
        choices=LANGUAGE_DICT.keys(),
        required=False,
        nargs='?',
        default='en',
        const='en',
        type=str
    )
    args = parser.parse_args()
    return args


def signal_handler(signal, frame):
    print('\nYou pressed Ctrl+C, keyboardInterrupt detected!')
    sys.exit(0)


def monitor_stats(stats_dict, stop_event, interval=1.0):
    """
    Monitors statistics from all workers and displays a single line with
    total address count and generation speed.
    """
    last_total_count = 0
    last_time = time.time()
    while not stop_event.is_set():
        time.sleep(interval)
        now = time.time()
        # Sum the total addresses generated across all workers
        total_count = sum(count for count, _ in stats_dict.values())
        dt = now - last_time
        dc = total_count - last_total_count
        speed = (dc / dt) if dt > 0 else 0
        print(f"\rGenerated addresses: {total_count} | Speed: {speed:.2f} addr/sec", end='', flush=True)
        last_total_count = total_count
        last_time = now


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    signal.signal(signal.SIGINT, signal_handler)
    args = Arguments()
    mnemonic_lenght = args.lenght
    entropy = WORDS_ENTROPY.get(mnemonic_lenght)
    lang_dict = LANGUAGE_DICT.get(args.dict)
    if not bool(re.match(SIGNUM_ADDRESS_MASK, args.match)):
        print(f'[!] Mask must only contain {MASK[1:-2]}')
        exit()
    match = (
        args.match
        .replace('?', '\\S')
        .replace('#', '\\d')
        .replace('@', '\\w')
    )
    logging.info(f'Generating address using mask {args.match} with a mnemonic length of {mnemonic_lenght} words')
    
    with mp.Manager() as manager:
        result_queue = manager.Queue()
        stop_event = manager.Event()
        stats_dict = manager.dict()
        processes = []
        
        logging.info("Using CPU for address generation")
        # Start CPU worker processes
        for i in range(PROCESSES):
            stats_dict[i] = (0, time.time())
            p = mp.Process(
                target=worker,
                args=(match, args.salt, entropy, lang_dict, Mnemonic, result_queue, stop_event, i, stats_dict)
            )
            p.start()
            processes.append(p)
            logging.info(f"Started CPU worker process {i+1}/{PROCESSES}")
        
        # Start monitoring process
        monitor_proc = mp.Process(target=monitor_stats, args=(stats_dict, stop_event))
        monitor_proc.start()
        
        # Wait for a result
        result = result_queue.get()
        stop_event.set()  # Signal all processes to stop
        
        # Wait for all processes to terminate
        for p in processes:
            p.join()
        
        monitor_proc.join()
        
        # Clear the last status line
        print()
        
        print("\nYour new passphrase is: \n\t" + result['passphrase'] + "\n")
        print("Address        : ", result['address'])
        print(f"Attempts: {result['attempts']}, Worker: {result['worker_id']}, Time: {result['total_time']:.2f} sec")
