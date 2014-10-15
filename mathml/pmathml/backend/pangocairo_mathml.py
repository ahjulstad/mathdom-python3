## This driver uses the Cairo 2D library together with Pango

import mathml
import warnings
import pango
import pangocairo


class PangoCairoPlotter(mathml.plotter.Plotter):
    def __init__(self, cr, pt_resolution):
	"""@cr: a cairo.Context instance;
	@pt_resolution: cairo units per 'point' (pt)"""
	self.cr = cr
	self.pt_resolution = pt_resolution
        self.have_path = False
        self.fontdesc = pango.FontDescription("Sans")
        self.height = 0
        self.cr.move_to(0, self.height)

    def set_cairo_context(self, new_cr):
        self.cr = new_cr
        self.cr.move_to(0, self.height)

    def moveto(self, x, y):
        if self.have_path:
            self.cr.stroke()
            self.have_path = False
        self.cr.move_to(x, self.height - y)

    def lineto(self, x, y):
	self.cr.line_to(x, self.height - y)
        self.have_path = True

    def linewidth(self, width):
	self.cr.set_line_width(width)

    def setfont(self, family, style, size):
        if style == "Regular":
            style = ""
	self.fontdesc = pango.FontDescription(' '.join((family, style, str(size))))

    def labelmetrics(self, text, logicalw=False):
        #logicalw = True #######################
	#Returns: layout, width, height, axis
        layout = self.cr.create_layout()
        layout.set_single_paragraph_mode(True)
        layout.set_font_description(self.fontdesc)
        layout.set_text(text)
        strikethroughs = []
        line = layout.get_line(0)
        for item, glstr in line.runs:
            font = item.analysis_font
            strikethroughs.append(font.get_metrics().get_strikethrough_position())
        strikethrough_pos = sum(strikethroughs)/len(strikethroughs)/pango.SCALE
        ink_rect, logical_rect = line.get_pixel_extents()
        if logicalw:
            _, y, _____, height = ink_rect
            x, _, width, ______ = logical_rect
        else:
            _, y, width, height = ink_rect
        descent = y + height
	return ((layout, ink_rect, logical_rect), # callback data
		width, height,
		descent + strikethrough_pos)

    def label(self, text, data=None, logicalw=False):
        #logicalw = True #######################
        if self.have_path:
            self.cr.stroke()
            self.have_path = False
	if data is None:
            layout = self.cr.create_layout()
            layout.set_single_paragraph_mode(True)
            layout.set_font_description(self.fontdesc)
            layout.set_text(text)
            line = layout.get_line(0)
            ink_rect, logical_rect = line.get_pixel_extents()
        else:
            layout, ink_rect, logical_rect = data

        ix, iy, iwidth, iheight = ink_rect
        lx, ly, lwidth, lheight = logical_rect
        descent = iy + iheight
        if logicalw:
            x0 = lx
        else:
            x0 = ix
        self.cr.rel_move_to(-x0, ly - descent)
        self.cr.show_layout(layout)
        self.cr.rel_move_to(x0, -(ly - descent))

    def savestate(self):
        if self.have_path:
            self.cr.stroke()
            self.have_path = False
	self.cr.save()

    def restorestate(self):
        if self.have_path:
            self.cr.stroke()
            self.have_path = False
	self.cr.restore()

    def translate(self, x, y):
        if self.have_path:
            self.cr.stroke()
            self.have_path = False
	self.cr.translate(x, -y)

    def resolve_length(self, value, unit):
	if unit == 'pt':
	    return self.pt_resolution * value
	warnings.warn("Cannot resolve unit '%s'" % (unit, ))
	return value

    def setcliprect(self, x1, y1, x2, y2):
        if self.have_path:
            self.cr.stroke()
            self.have_path = False
        self.cr.rectangle(x1, self.height - y1, x2 - x1, y1 - y2)
        self.cr.clip()

    def close(self):
        if self.have_path:
            self.cr.stroke()
            self.have_path = False
        
