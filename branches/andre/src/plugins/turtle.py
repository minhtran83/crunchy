#Typical usage would probably be
#>>>from turtle import *
#then just treat it like a logo interpreter

import math, inspect
import math_graphics as g
import src.CrunchyPlugin as __cp

(angle, x, y, draw, log, logf) = (0, 0, 0, True, True, [])

def init_graphics(width=640, height=480):
	'''Initialize turtle drawing routines'''
	g.init_graphics(width, height)
	_log_action(1)
	_draw_turtle()

def forward(len):
	'''Send turtle forward'''
	global x, y, angle
	deltay = len * math.sin( math.radians(angle) )
	deltax = len * math.cos( math.radians(angle) )
	line(x+deltax, y+deltay)

def backward(len):
	'''Send turtle backward'''
	forward(-len)

def left(theta):
	'''Rotate turtle left by degrees'''
	right(-theta)

def right(theta):
	'''Rotate turtle right by degrees'''
	global angle
	angle -= theta
	while (angle < 0):
		angle += 360
	while (angle >= 360):
		angle -= 360
	_erase_turtle()
	_draw_turtle()

def home():
	'''Sends to turtle back to (0,0)'''
	goto(0, 0)

def goto(xc, yc):
	'''Sends turtle to specified coordinates (draws if applicable)'''
	xc = x - xc
	yc = y - yc
	line( xc, yc )

def line(xc, yc):
	'''Moves turtle to specified relative coordinates'''
	global x, y
	_erase_turtle()
	if draw:
		g.line((x, y),(xc, yc))
	(x, y) = (xc, yc)
	_draw_turtle()

def circle(r):
	'''Draws a circle (optionally filled)'''
	global x, y
	_erase_turtle()
	if draw:
		g.circle( (x,y), r)
	_draw_turtle()

def pen_up():
	'''Stops drawing'''
	global draw
	draw = False
	_log_action(1)

def pen_down():
	'''Resumes drawing'''
	global draw
	draw = True
	_log_action(1)

def set_color(line):
	'''Sets line color'''
	g.set_line_color(line)
	_log_action(1)

set_colour = set_color

def _erase_turtle():
	global log
	
	print "Turtle erase"
	_log_action(2)
	log = False
	_replay_log()
	log = True
	
def _draw_turtle():
	'''Draw the turtle'''
	_save_canvas()

	global x, y, angle	
	xd = lambda v: math.cos( math.radians( v+angle ) )
	yd = lambda v: math.sin( math.radians( v+angle ) )
	
	g.set_fill_color('NavajoWhite')
	#turtle feet
	for i in (45,135,225,315):
		g.filled_circle( (x+(27*xd(i)),y+(27*yd(i))), 10 )
	#a head of sorts
	g.filled_circle( (x+(30*xd(0)),y+30*yd(0)), 10 )
	#and a nice shell
	g.set_fill_color('ForestGreen')
	g.filled_circle( (x,y), 25 )
	
	_restore_canvas()

def _save_canvas():
	'''Saves the current canvas'''
	uid = __cp.get_uid()
	__cp.exec_js(__cp.get_pageid(),"""document.getElementById("canvas_%s").getContext('2d').save();"""%uid)

def _restore_canvas():
	'''Restores the last saved canvas'''
	uid = __cp.get_uid()
	__cp.exec_js(__cp.get_pageid(),"""document.getElementById("canvas_%s").getContext('2d').restore();"""%uid)
	
def _log_action(level):
	'''Log the caller (or above) function and the arguments passed to it'''
	global log, logf

	if not log:
		return
	str = inspect.stack()[level][3]
	str += '('
	
	them = inspect.stack()[level][0]
	try:
		arginfo = inspect.getargvalues(them)
	except:
		pass
	finally:
		del them	#help prevent memory leaks
	argsdict = arginfo[3]
	args_str = ''

	for arg in arginfo[0]:
		subarg = "%s" %argsdict[arg]
		args_str += ','+subarg
	args_str = args_str[1:]	#cut off the leading comma
	str += args_str+')'
	
	logf.append(str)
	print "Log:%s" %str

def _replay_log():
	'''Replay saved actions in logf'''
	global logf, log
	
	if not log:
		return
	init_graphics(0,0)
	localvars = {'x':0,'y':0,'angle':0,'draw':True,'log':False}
	
	for statement in logf:
		exec statement #in localvars
		print "Log replay: %s" %statement