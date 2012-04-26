def HSVtoRGB(h, s, v):
	"""
	0 <= H < 360
	0 <= S < 1
	0 <= V < 1
	"""

	c = v * s
	h2 = h / 60
	x = c * (1 - abs((h2 % 2) - 1))

	if h2 < 1:
		r, g, b = c, x, 0
	elif h2 < 2:
		r, g, b = x, c, 0
	elif h2 < 3:
		r, g, b = 0, c, x
	elif h2 < 4:
		r, g, b = 0, x, c
	elif h2 < 5:
		r, g, b = x, 0, c
	elif h2 < 6:
		r, g, b = c, 0, x
	
	m = v - c
	return r + m, g + m, b + m

if __name__ == "__main__":
	h = 30.0
	v = 1.0

	for s in range(0, 100 + 1, 10):
		r, g, b = HSVtoRGB(h, s / 100.0, v)
		hexcolor = "#%02x%02x%02x" % (r * 0xff, g * 0xff, b * 0xff)
		print "<div style=\"background: %s\">%s</div>" % (hexcolor, hexcolor)