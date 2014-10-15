from mathml.pmathml.element import *
from mathml.pmathml.mtoken import MToken
import xml.sax.handler

class MathMLHandler(xml.sax.handler.ContentHandler):
    class Elem(object):
	__slots__ = ('parent', 'name', 'attributes', 'text', 'children')
	
    def __init__(self, plotter):
	self.plotter   = plotter
	self.current   = self.Elem()
	self.current.children = []

    def characters(self, content):
	self.current.text += content

    def startElementNS(self, xxx_todo_changeme, qname, attrs):
	(ns, name) = xxx_todo_changeme
	elem = self.Elem()
	elem.parent = self.current
	elem.parent.children.append(elem)
	elem.text = ''
	elem.attributes = {}
	for key, value in list(attrs.items()):
	    elem.attributes[key] = value
	elem.children = []
	elem.name = name
	self.current = elem

    def endElementNS(self, xxx_todo_changeme1, qname):
	(ns, name) = xxx_todo_changeme1
	self.current = self.current.parent

    def __buildTreeRecursive(self, node):
	klass = xml_mapping[node.name]
	if issubclass(klass, MToken):
	    element = klass(self.plotter, node.text.strip())
	else:
	    children = list(map(self.__buildTreeRecursive, node.children))
	    element = klass(self.plotter, children)
	for name, value in list(node.attributes.items()):
	    element.setAttribute(name, value)
	return element

    def buildTree(self):
	assert len(self.current.children) == 1
	elem = self.__buildTreeRecursive(self.current.children[0])
	del self.current
	return elem


def buildFromPMathml(etree, plotter):
    handler = MathMLHandler(plotter)
    etree.saxify(handler)
    return handler.buildTree()

def buildFromMathDOM(mathdom, plotter):
    return buildFromPMathml(mathdom.to_pmathml(), plotter)
