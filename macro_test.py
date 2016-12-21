
from lxml import etree
import conf_py

p = conf_py.conf_page()
p.tree.append(p.macro1(p.macro2(), p.macro3()))
print p.get_string()

