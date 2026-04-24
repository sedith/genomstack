from genomstack import Robot

r = Robot('tilthex_simu')

r.setup()
r.spin()
r.start(prompt=True)

r.goto(-5, 2, 3, 1, prompt=True)
r.land(prompt=True)

r.stop(prompt=True)
