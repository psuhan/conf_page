
# -*- coding: utf-8 -*-
class node(object):

	def __init__(self, tag, text=''):
		self.tag = tag
		self.prop = {}
		self.child = []
		self.text = text

	def getchild(self):
		return self.child

	def setchild(self, child):
		self.child.append(child)

	def settext(self, text):
		self.text = text	

	def setprop(self, key, val):
		self.prop[key] = val

	def tostring(self):
		#head tag
		ret = '<{}'.format(self.tag)
		for (key, val) in self.prop.items():
			ret = ret + ' {}={}'.format(key, val)
		ret = ret + '>{}'.format(self.text)
		for child in self.child:
			ret = ret + child.tostring()
		#tail tag
		ret = ret + '</{}>'.format(self.tag)
		return ret

	def find(self, tag):
		if self.tag == tag:
			ll = [self]
		else:
			ll = []
		for c in self.getchild():
			ll = ll + c.find(tag)
		return ll

	def striptag(self, string):
		string = string.strip()
		print string
		a = string.find('<')
		b = string.find('>')
		tag = string[a+1:b].split()[0]
		return (tag, string[b+1:])

	def striptext(self, string):
		string = string.strip()
		a = string.find('<')
		text = string[0:a]
		return (text, string[a:])

	def fromstring(self, string):
		(tag, string) = self.striptag(string)
		(text, string) = self.striptext(string)
		print 'tag: {}, text: {}'.format(tag, text)
		while(True):
			(tag2, temp) = self.striptag(string)
			if tag2 == '/{}'.format(tag):
				string = temp
				return True
			else:
				print 'adding new child with tag: {}'.format(tag)
				child = node(tag)
				child.settext(text)
				child.fromstring(string)

if __name__ == '__main__':
	
	#a = node('div')
	#b = node('p', 'this is b')
	#c = node('p', 'this is c')
	#b.setprop('class', '"doremi"')
	#c.setprop('class', '"mifaso"')
	#a.setchild(b)
	#a.setchild(c)
	#print a.tostring()
	#for t in a.find('p'):
	#	print t.tag
	src = '<ac:layout><ac:layout-section ac:type=\"two_equal\"><ac:layout-cell><p class=\"auto-cursor-target\"><br /></p><table><colgroup><col /><col /><col /></colgroup><tbody><tr><th>table</th><th>A</th><th>B</th></tr><tr><td>row added</td><td>automatically</td><td>Thu Dec 22 00:35:04 2016</td></tr><tr><td>do</td><td>re</td><td>mi</td></tr></tbody></table><p class=\"auto-cursor-target\"><br /></p></ac:layout-cell><ac:layout-cell><p class=\"auto-cursor-target\"><br /></p><ac:structured-macro ac:name=\"chart\" ac:schema-version=\"1\" ac:macro-id=\"f1839e86-5974-4fde-879e-bc6795c7be57\"><ac:parameter ac:name=\"subTitle\">Contribution</ac:parameter><ac:parameter ac:name=\"width\">300</ac:parameter><ac:parameter ac:name=\"dataOrientation\">vertical</ac:parameter><ac:parameter ac:name=\"title\">PIE</ac:parameter><ac:parameter ac:name=\"height\">300</ac:parameter><ac:rich-text-body><p class=\"auto-cursor-target\"><br /></p><table><colgroup><col style=\"width: 32.0px;\" /><col style=\"width: 52.0px;\" /></colgroup><tbody><tr><th>time</th><th>ratio</th></tr><tr><td colspan=\"1\">A</td><td colspan=\"1\">30</td></tr><tr><td>B</td><td>45</td></tr><tr><td>C</td><td>35</td></tr></tbody></table><p class=\"auto-cursor-target\"><br /></p></ac:rich-text-body></ac:structured-macro><p class=\"auto-cursor-target\"><br /></p></ac:layout-cell></ac:layout-section><ac:layout-section ac:type=\"single\"><ac:layout-cell><p class=\"auto-cursor-target\"><br /></p><ac:structured-macro ac:name=\"excerpt\" ac:schema-version=\"1\" ac:macro-id=\"b90b4b68-4f52-4117-9867-f1d479b21020\"><ac:parameter ac:name=\"atlassian-macro-output-type\">BLOCK</ac:parameter><ac:rich-text-body><p>발췌내용</p></ac:rich-text-body></ac:structured-macro><p class=\"auto-cursor-target\"><br /></p></ac:layout-cell></ac:layout-section></ac:layout>'

	d = node('root')
	d.fromstring(src)
	#print d.tostring()
