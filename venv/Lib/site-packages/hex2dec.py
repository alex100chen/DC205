import sys

def dec2hex(n):
    """return the hexadecimal string representation of integer n"""
    return "%X" % n

def hex2dec(s):
    """return the integer value of a hexadecimal string s"""
    return int(s, 16)


def main(n,hd):
	if hd == "hex": 
		print "Hex:", n, "\nDec:", hex2dec(n)
	elif hd == "dec":
		print dec2hex(n)


if __name__ == "__main__":
    main(sys.argv[1],sys.argv[2])
