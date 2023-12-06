"""
pyburstlib
:author: gittrekt
:date: 8-22-2023

Signum RS Generator
Simple function to generate a Signum RS address from an account ID
"""

alphabet = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
cwmap = [3, 2, 1, 0, 7, 6, 5, 4, 13, 14, 15, 16, 12, 8, 9, 10, 11]
gexp = [1, 2, 4, 8, 16, 5, 10, 20, 13, 26, 17, 7, 14, 28, 29, 31, 27, 19, 3, 6, 12, 24, 21, 15, 30, 25, 23, 11, 22, 9, 18, 1]  # noqa: E501
glog = [0, 0, 1, 18, 2, 5, 19, 11, 3, 29, 6, 27, 20, 8, 12, 23, 4, 10, 30, 17, 7, 22, 28, 26, 21, 25, 9, 16, 13, 14, 24, 15]  # noqa: E501


def get_address(account_id: int = 0) -> str:
    codeword = [1] * 17
    p = [0] * 4
    addr = 'S-'

    for i in range(13):  # Create the codeword
        codeword[i] = (int(account_id) >> (5 * i)) & 31

    for i in range(12, -1, -1):  # Encode the codeword
        fb = codeword[i] ^ p[3]
        p[3] = p[2] ^ gmult(30, fb)
        p[2] = p[1] ^ gmult(6, fb)
        p[1] = p[0] ^ gmult(9, fb)
        p[0] = gmult(17, fb)
    codeword[13] = p[0]
    codeword[14] = p[1]
    codeword[15] = p[2]
    codeword[16] = p[3]

    for i in range(17):
        addr += alphabet[codeword[cwmap[i]]]  # Lookup the address
        if i & 3 == 3 and i < 13:  # Add dashes
            addr += '-'

    return addr


def gmult(a, b):
    if (a == 0 or b == 0):
        return 0

    idx = (glog[a] + glog[b]) % 31

    return gexp[idx]
