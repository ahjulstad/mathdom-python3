from .element import *
import warnings
from . import opdict
import re

# --- FONT NAMES ---
if 1:
    # experimental fonts...
    MI_FONT_REGULAR = ('Sans', 'Regular')
    MI_FONT_ITALIC  = ('Sans', 'Italic')
    MO_FONT_REGULAR = ('Sans', 'Regular')
    MO_FONT_ITALIC  = ('Sans', 'Italic')
    MN_FONT         = ('Sans', 'Regular')
    MTEXT_FONT      = ('Sans', 'Regular')
    MERROR_FONT     = ('Monospace', 'Regular')
elif 0:
    # experimental fonts...
    MI_FONT_REGULAR = ('cmr10', 'Regular')
    MI_FONT_ITALIC  = ('cmmi10', 'Regular')
    MO_FONT_REGULAR = ('cmr10', 'Regular')
    MO_FONT_ITALIC  = ('cmmi10', 'Regular')
    MN_FONT         = ('cmr10', 'Regular')
    MTEXT_FONT      = ('Sans', 'Regular')
    MERROR_FONT     = ('Monospace', 'Regular')
else:
    MI_FONT_REGULAR = ('URW Palladio L', 'Roman')
    MI_FONT_ITALIC  = ('URW Palladio L', 'Italic')
    MO_FONT_REGULAR = ('URW Palladio L', 'Roman')
    MO_FONT_ITALIC  = ('URW Palladio L', 'Italic')
    MN_FONT         = ('URW Bookman L', 'Light')
    MTEXT_FONT      = ('Serif', 'Regular')
    MERROR_FONT     = ('Times', 'Regular')




class _StretchyParts(object):
    __slots__ = ('upper', 'lower', 'middle', 'bar')
    def __init__(self, upper, lower, bar, middle=None):
	self.upper  = upper
	self.lower  = lower
	self.middle = middle
	self.bar    = bar
	

# pieces that make up a stretchy operator: upper, middle, and lower parts.
_stretchy_parenthesis = {
    '(': _StretchyParts(upper=chr(0x239b), bar=chr(0x239c), lower=chr(0x239d)),
    '[': _StretchyParts(upper=chr(0x23a1), bar=chr(0x23a2), lower=chr(0x23a3)),
    '{': _StretchyParts(upper=chr(0x23a7), middle=chr(0x23a8),
			lower=chr(0x23a9), bar=chr(0x23aa)),
    ')': _StretchyParts(upper=chr(0x239e), bar=chr(0x239f), lower=chr(0x23a0)),
    ']': _StretchyParts(upper=chr(0x23a4), bar=chr(0x23a5), lower=chr(0x23a6)),
    '}': _StretchyParts(upper=chr(0x23ab), middle=chr(0x23ac),
			lower=chr(0x23ad), bar=chr(0x23aa)),
    chr(0x222B): # integral  http://home.att.net/~jameskass/code2000_page.htm
    _StretchyParts(upper=chr(0x2320),
                   lower=chr(0x2321),
                   bar=chr(0x23ae)),
    '|': _StretchyParts(upper=None, lower=None, bar=chr(0x23ae)),
    }

content_substitutions = {
    chr(0x02145): 'D', # &CapitalDifferentialD;
    chr(0x02146): 'd', # &DifferentialD;
    chr(0x02147): 'e', # &ExponentialE;
    chr(0x02148): 'i', # &ImaginaryI;
    '-':             '\N{MINUS SIGN}',
    chr(0x02AA1): '\N{MUCH LESS-THAN}', # &LessLess;
    chr(0x02AA2): '\N{MUCH GREATER-THAN}', # &GreaterGreater;
    chr(0x02254): '\N{COLON EQUALS}', # assignment operator
    }

_content_substitutions_rx = re.compile("|".join(map(re.escape, list(content_substitutions.keys()))))


# --------------------------------------------------------

class MToken(Element):

    def __init__(self, plotter, content):
	Element.__init__(self, plotter)
	self.content = content	
	self.descender = 0
	self.__stretch_height = None
	self.__stretch_depth  = None
	self.__stretch_width  = None
	self.__parts = None
	#self.__stretchy_font_family = "Standard Symbols L"
        #self.__stretchy_font_family = "Code2000"
        self.__stretchy_font_family = "FreeSerif"
	self.__stretchy_font_style = "Regular"
	if (self.content == chr(0x2062) or # &InvisibleTimes;
	    self.content == chr(0x2061)    # &ApplyFuncion;
	    ):
	    self.setAttributeWeak("lspace", 0.0)
	    self.setAttributeWeak("rspace", 0.0)
	self._applySubstitutions()

    def _applySubstitutions(self):
	self.subst_content = _content_substitutions_rx.sub(
	    lambda match: content_substitutions[match.group(0)], self.content)
	
    def _update_stretchy(self):
	pl = self.plotter

	pl.setfont(self.__stretchy_font_family,
		   self.__stretchy_font_style,
		   self.font_size)
	default_min_height = 0
	for part in (self.__parts.lower,
		     self.__parts.middle,
		     self.__parts.upper):
	    if part is None: continue
	    _, _, height, _ = pl.labelmetrics(part)
	    default_min_height += height

	# make sure font is never shrinked more than half, even if
	# that means stretching a bit more than requested.
	if default_min_height*0.5 > self.__stretch_depth + self.__stretch_height:
	    self.height = default_min_height*0.5
	    k = self.__stretch_depth / (self.__stretch_depth + self.__stretch_height)
	    self.__stretch_depth = self.height*k
	    self.__stretch_height = self.height - self.__stretch_depth
	    self.__stretched_font_size = self.font_size*0.5
	else:
	    self.height = self.__stretch_depth + self.__stretch_height
	    if default_min_height > self.height:
		self.__stretched_font_size = self.height/default_min_height*self.font_size
	    else:
		self.__stretched_font_size = self.font_size

	pl.setfont(self.__stretchy_font_family,
		   self.__stretchy_font_style,
		   self.__stretched_font_size)
        self.width = 0
	for part in (self.__parts.lower,
		     self.__parts.middle,
		     self.__parts.upper,
                     self.__parts.bar):
	    if part is not None:
                _, width, _, _ = pl.labelmetrics(part, logicalw=True)
                self.width = max(self.width, width)
	self.axis = self.__stretch_depth
	
    def update(self):
	# Delegate horizontal/vertical stretching
	if self.__stretch_width:
	    return self._update_hstretchy()
	elif self.__parts is not None:
	    return self._update_stretchy()

	if (self.content == chr(0x2062) or # &InvisibleTimes;
	    self.content == chr(0x2061)):  # &ApplyFunction;

	    self.width = self.Attribute(self, "verythinmathspace").length
	    self.height = 0
	    return
	
	pl = self.plotter
	pl.setfont(self.font_family, self.font_style, self.font_size)
	self.__layout_cache, self.width, self.height, self.axis =\
		pl.labelmetrics(self.subst_content)
	self.unstretched_width  = self.width
	self.unstretched_height = self.height

    def setVStretch(self, height, depth):
	#print "setVStrectch(height=%f, depth=%f)" % (height, depth)
	self.__stretch_height = height
	self.__stretch_depth  = depth
	try:
	    self.__parts = _stretchy_parenthesis[self.content]
	except KeyError:
	    self.__parts = None
	    warnings.warn("Cannot stretch '%s'" %
			  ",".join([hex(ord(c)) for c in self.content]))

    def setHStretch(self, width):
	self.__stretch_width = width

    def _draw_non_stretchy(self):
	pl = self.plotter
	pl.setfont(self.font_family, self.font_style, self.font_size)
	pl.moveto(0, 0)
	pl.label(self.subst_content, self.__layout_cache)

    def _close_gap(self, gap_start, gap_end, bar, x0):
	if gap_start >= gap_end:
	    #print("Warning: '%s': gap_start = %f; gap_end = %f" %
	    #  (self.content, gap_start, gap_end))
	    return
	pl = self.plotter
	layout, width, height, _ = pl.labelmetrics(bar, logicalw=True)
	if height <= 0: return # height == 0 produces an infinite loop!

        overlap = height/20
        jump = height - overlap
        gap_start -= overlap
        gap_end += overlap
        
	y = gap_start
	while y < gap_end:
            if y + height > gap_end:
		pl.savestate()
		pl.setcliprect(-width, y, width*2, gap_end)
                pl.moveto(x0, y)
		pl.label(bar, layout, logicalw=True)
		pl.restorestate()
	    else:
                pl.moveto(x0, y)
		pl.label(bar, layout, logicalw=True)
	    y += jump

    def _draw_stretchy(self):
	pl = self.plotter
	pl.setfont(self.__stretchy_font_family, self.__stretchy_font_style,
		   self.__stretched_font_size)

	# Lower part
        if self.__parts.lower is not None:
            layout, width, lower_gap_start, _ = pl.labelmetrics(self.__parts.lower, logicalw=True)
            pl.moveto(0, 0)
            pl.label(self.__parts.lower, layout, logicalw=True)
        else:
            lower_gap_start = 0

	# Upper part
        if self.__parts.upper is not None:
            layout, width, height, _ = pl.labelmetrics(self.__parts.upper)
            upper_gap_end = self.height - height
            pl.moveto(0, upper_gap_end)
            pl.label(self.__parts.upper, layout,  logicalw=True)
        else:
            upper_gap_end = self.height

	if self.__parts.middle is None:
            # No middle part
	    self._close_gap(lower_gap_start, upper_gap_end,
			    self.__parts.bar, 0)
	else:
	    # Have a middle part
	    layout, _, height, _ = pl.labelmetrics(self.__parts.middle, logicalw=True)
	    lower_gap_end = self.__stretch_depth - height/2
	    pl.moveto(0, lower_gap_end)
	    pl.label(self.__parts.middle, layout, logicalw=True)
	    upper_gap_start = lower_gap_end + height
	    self._close_gap(lower_gap_start, lower_gap_end,
			    self.__parts.bar, 0)
	    self._close_gap(upper_gap_start, upper_gap_end,
			    self.__parts.bar, 0)
	    
    def draw(self):
	if (self.content == chr(0x2062) or
	    self.content == chr(0x2061)):
	    return
	if self.__stretch_width is not None:
	    self._draw_hstretchy()
	elif self.__parts is not None:
	    self._draw_stretchy()
	else:
	    self._draw_non_stretchy()

    def _update_hstretchy(self):
	## This is called "Lazy Horizontal Stretching (TM)": just
	## scale the font to make the label as wide as needed :P
	pl = self.plotter
	pl.setfont(self.font_family, self.font_style, self.font_size)
	_, width, height, axis = pl.labelmetrics(self.subst_content)
	scaling = self.__stretch_width/width

	self.__stretched_font_size = self.font_size*scaling
	pl.setfont(self.font_family, self.font_style, self.__stretched_font_size)
	_, self.width, self.height, self.axis = pl.labelmetrics(self.subst_content)

    def _draw_hstretchy(self):
	pl = self.plotter
	pl.setfont(self.font_family, self.font_style, self.__stretched_font_size)
	pl.moveto(0, 0)
	pl.label(self.subst_content, self.__layout_cache)
	

    def __str__(self):
	return str(self.__class__) + "('"+self.content+"')"

class MText(MToken):
    def __init__(self, plotter, content):
	MToken.__init__(self, plotter, content)
	self.font_family = MTEXT_FONT[0]
	self.font_style  = MTEXT_FONT[1]

class MError(MToken):
    def __init__(self, plotter, content):
	MToken.__init__(self, plotter, content)
	self.font_family = MERROR_FONT[0]
	self.font_style  = MERROR_FONT[1]

class MOperator(MToken):
    def __init__(self, plotter, content):
	MToken.__init__(self, plotter, content)
	self.__original_content = content
	self.font_family = MO_FONT_REGULAR[0]
	self.font_style  = MO_FONT_REGULAR[1]

    def update(self):
	form = self.getAttribute("form", recursive=0, default="infix").str
	try:
	    attrs = opdict.lookup(self.__original_content, form)
	    #print "found opdict entry for ", self.__original_content, ":"
	    for key, value in list(attrs.items()):
		#print "%s => %s" % (key, value)
		self.setAttributeWeak(key, value)
	except KeyError:
	    warnings.warn("Couldn't find operator '%s' in operator dictionary" % (self.content, ))
	#if self.content == '-':
	#    self.content = unichr(0x2212)
	MToken.update(self)

    def embellished_p(self):
	return self


class MNumber(MToken):
    def __init__(self, plotter, content):
	MToken.__init__(self, plotter, content)
	self.font_family = MN_FONT[0]
	self.font_style  = MN_FONT[1]

class MIdentifier(MToken):
    def __init__(self, plotter, content):
	MToken.__init__(self, plotter, content)
	if len(content) > 1:
	    self.font_family = MI_FONT_REGULAR[0]
	    self.font_style  = MI_FONT_REGULAR[1]
	else:
	    self.font_family = MI_FONT_ITALIC[0]
	    self.font_style  = MI_FONT_ITALIC[1]

# __all__ = (
#     'MText',
#     'MOperator',
#     'MNumber',
#     'MIdentifier')

xml_mapping['mtext']  = MText
xml_mapping['merror'] = MError
xml_mapping['mo']     = MOperator
xml_mapping['mi']     = MIdentifier
xml_mapping['mn']     = MNumber

