"""
Collection of various utility functions for cryptoanalysis.
"""

import string, collections, os, signal
import gmpy
from functools import wraps
from itertools import *
from random import seed, randint

import freq

# The expected index of coincidence value for English text
ic_english = 0.065

def index_of_coincidence(frequencies, n):
    """
    Calculate the index of coincidence of a frequency
    distribution relative to the text length.

    Args:
        frequencies: the target frequencies to compare the text to.
        n: length of the text that the IC should be calculated for.

    Returns:
        the index of coincidence of a text of length n with the frequency
        distribution frequencies.
    """
    combinations = sum([f * (f - 1) for f in frequencies.values()])
    pairs = n * (n - 1)
    return float(combinations) / float(pairs) if pairs > 0 else 0

def expected_ic(frequencies=freq.english):
    """
    Calculate the expected index of coincidence for a text having
    the specified frequency distribution.

    Args:
        frequencies: the target frequency distribution.

    Returns:
        the expected index of coincidence for a text matching
        the frequency distribution passed
    """
    return sum([f * f for f in frequencies.values()])

def squared_differences(frequencies, expected=freq.english):
    pairs = zip(frequencies.values(), expected.values())
    return sum([(f - e) ** 2 for f,e in pairs])

def chi_squared(counts, length, expected=freq.english):
    expectedcount = {c: e * length for c,e in expected.items()}
    pairs = zip(counts.values(), expected.values())
    return sum([((c - e) ** 2) / float(e) for c,e in pairs])

class TimeoutError(Exception):
    pass

# Timeout decorator
def timeout(seconds=10, error_message=""):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator

# Number theory
@timeout(10)
def fermat_factor(N):
    """
    Guess at a and hope that a^2 - N = b^2,
    which is the case if p and q is "too close".
    """
    a  = gmpy.sqrt(N)
    b2 = a*a - N
    while not gmpy.is_square(gmpy.mpz(b2)):
        b2 += 2*a + 1
        a  += 1

    factor1 = a - gmpy.sqrt(b2)
    factor2 = a + gmpy.sqrt(b2)
    return (int(factor1.digits()),int(factor2.digits()))

@timeout(10)
def factor_pollard_rho(N):
    """
    Pollard's rho algorithm for factoring numbers,
    implemented using Brent's cycle finding algorithm.
    """
    i = 1
    power = 2
    x = y = 2
    d = 1

    while d == 1:
        i += 1
        x = (x * x + 2) % N
        d = gcd(abs(x - y), N)

        if i == power:
            y = x
            power *= 2

    if d != N: return (d, N // d) # Whaat?
    else: return None

def factor(N):
    """Factor using the currently best implemented factoring algorithm"""
    return factor_pollard_rho(N)

def totient(p,q):
    """Eulers totient function"""
    return (p-1)*(q-1)

def egcd(a, b):
    """Extended greatest common denominator function"""
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)

def gcd(b, p):
    """Greatest common denominator (Euclids algorithm)"""
    return egcd(b, p)[0]

def modinv(a, m):
    """Modular multiplicative inverse, i.e. a^-1 = 1 (mod m)"""
    a, u, v = egcd(a, m)
    if a <> 1:
        raise Exception('No inverse: %d (mod %d)' % (b, p))
    return u

def crt(a, n):
    """Solve Chinese remainder theorem, eg. determine x in
    a[0] = x       ( n[0] )
    ...
    a[-1] = x      ( n[-1] )

    Elements in n must be pairwise co-prime"""
    M = reduce(operator.mul, lm)
    # print M
    lM = [M/mi for mi in lm]
    ly = map(invmod, lM, lm)
    laMy = map((lambda ai, Mi, yi : ai*Mi*yi), la, lM, ly)
    return sum(laMy) % M

def reste_chinois(a, n):
    """Alias for crt"""
    return crt(a, n)

def fast_exponentiation(a, p, n):
    """A fast way to calculate a**p % n"""
    result = a%n
    remainders = []
    while p != 1:
        remainders.append(p & 1)
        p = p >> 1
    while remainders:
        rem = remainders.pop()
        result = ((a ** rem) * result ** 2) % n
    return result

