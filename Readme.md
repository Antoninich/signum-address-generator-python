# Signum Vanity Address Generator

## What is it?
Vanity Address Generator for the Signum Blockchain Platform

Create your personalized Signum Address, like `S-BEER-XYBN-2G34-H98GT`

When finding a new account address, you must activate it on first time that you send a transaction.

## Requirements
1. python3 installed
2. pip installed

## How to
1. Open a new terminal
2. Install requirements with the following command 
```text
pip install -r requirements.txt
```
3. Enter the following command 
```text
python vanity.py -m <YOUR DESIRED NAME>
```

example: `python vanity.py -m S-@@@@-@#@@-@#@@-?????`
eventually returns `S-USAB-U7JP-V2ZH-5PKKP`
# Help
```
Passphrase generator for vanity addresses on Signum cryptocurrency.

Usage: python vanity.py [OPTION]... -m MASK
Example: python vanity.py -m S-@@@@-@#@@-@#@@-?????

Options:
  -h, --help                               Show this help statement
  -d, --dict [en,fr,it,ja,ko,es,tr,cs,pt]  Dictionary language for bip-39. Default is english
  -s, --salt SALT                          Add your salt to the bip39 word list
  -l, --lenght [12,15,18,21,24]            Mnemonic lenght 12, 15, 18, 21, 24. Default: 12
  -m, --match                              Specify the rules for the desired address. Default: S-????-????-????-?????

Mask:
  Specify the rules for the desired address.
  It must be at least one char long.
  No 0, O, I or 1 are allowed.
  Following wildcars can be used:
    ?: Matches any char
    @: Matches only letters [A-Z]
    #: Matches only numbers [2-9]
    -: Use to organize the mask, does not affect result
```

# Inspiration
* https://github.com/deleterium/signum-vanity-opencl Fast Vanity Address Generator for the Signum Blockchain Platform.
* https://github.com/beatsbears/burst-vanity-generator
* https://github.com/gittrekt/pyburstlib