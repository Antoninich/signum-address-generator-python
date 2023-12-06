import argparse
import os
import re
import signal
import sys
from mnemonic import Mnemonic
import multiprocessing as mp

import libs.crypto as crypto


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


def generate_passphrase(salt, entropy, lang_dict):
    mnemo = Mnemonic(lang_dict)
    return mnemo.generate(strength=entropy) + salt


def signal_handler(signal, frame):
    print('\nYou pressed Ctrl+C, keyboardInterrupt detected!')
    sys.exit(0)


def is_match(match, address):
    if bool(re.match(match, address)):
        return True


def generate_wallet(match, salt, entropy, lang_dict):
    n = 0
    while not quit.is_set():
        passphrase = generate_passphrase(salt, entropy, lang_dict)
        address = crypto.get_account_address(passphrase)
        print(f"Address: {address}. Check {n} addresses", end='\r', flush=True)
        n += 1
        if is_match(match, address):
            quit.set()
            return {
                'passphrase': passphrase,
                'address': address,
            }


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    args = Arguments()
    match_arg = args.match
    mnemonic_lenght = args.lenght
    entropy = WORDS_ENTROPY.get(mnemonic_lenght)
    lang_dict = LANGUAGE_DICT.get(args.dict)
    match = ''
    if not bool(re.match(SIGNUM_ADDRESS_MASK, args.match)):
        print(f'[!] Mask must only contain {MASK[1:-2]}')
        exit()
    match = (
        args.match
        .replace('?', '\\S')
        .replace('#', '\\d')
        .replace('@', '\\w')
    )
    print(
        f'''An address is generated using mask {args.match} with
        a mnemonic length of {mnemonic_lenght} words'''
    )
    quit = mp.Event()
    with mp.Pool(processes=PROCESSES) as pool:
        result = pool.apply(
            generate_wallet,
            (match, args.salt, entropy, lang_dict)
        )
        print("\nYour new passprhase is: \n\t" + result['passphrase'] + "\n")
        print("Address        : ", result['address'])
