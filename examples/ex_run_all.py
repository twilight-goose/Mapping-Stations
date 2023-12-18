import ex1
import ex2
import ex4
import ex5
import ex6
import ex7
import ex8
import ex9
import ex10
import ex11
import ex12

import argparse

"""
Run all examples excluding ex8 (which is the slowest)
>>> python ex_run_all.py

Run ALL examples
>>> python ex_run_all.py -m s
"""

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description='''Run all examples''')
parser.add_argument('-m', '--method', action='store', default='f', dest='method',
                    help="Run method. 'f' (fast; skips ex8) or 's' (slow; runs all examples).")

method = parser.parse_args().method

if method not in ('f', 's'):
    print(f"Method argument '{method}' is invalid. Using the default f (fast)")
    method = 'f'

print("Starting ex1\n")
ex1.main(timed=True)

print("\nStarting ex2\n")
ex2.main(timed=True)

print("\nStarting ex4\n")
ex4.main(timed=True)

print("\nStarting ex5\n")
ex5.main(timed=True)

print("\nStarting ex6\n")
ex6.main(timed=True)

print("\nStarting ex7\n")
ex7.main()

if method == 's':
    print("\nStarting ex8\n")
    ex8.main()

print("\nStarting ex9\n")
ex9.main()

print("\nStarting ex10\n")
ex10.main()

print("\nStarting ex11\n")
ex11.main()

print("\nStarting ex12\n")
ex12.main()
