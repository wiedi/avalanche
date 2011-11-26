#!/usr/bin/env python2.6

import markdown
import jinja2
import codecs
import tempfile
import os
import sys
from subprocess import Popen, PIPE, call

DEFAULT_ENCODING = 'utf8'
W3_PREFIX = '/opt/local/bin/w3hx'


class Avalanche(object):
	
	def render_markdown(self, files):
		html = ""
		for f in files:
			if not f: continue
			text = codecs.open(f, mode="r", encoding=DEFAULT_ENCODING).read()
			html += markdown.markdown(text)
		
		return html	
		
	def render_theme(self, theme, context):
		template_src = codecs.open(theme + '/base.html', encoding=DEFAULT_ENCODING)
		template = jinja2.Template(template_src.read())
		context['print_css'] = codecs.open(theme + '/base.css', encoding=DEFAULT_ENCODING).read()
		html = template.render(context)
		return html
		
	def render(self):
		intro   = self.render_markdown(self.config['intro'])
		content = self.render_markdown(self.config['source'])
		context = {
			'intro':   intro,
			'content': content,
			'title': self.config['title'],
			'toc_enabled': self.config['toc_enabled']
		}
		return self.render_theme(self.config['theme'], context)
		
		
	def write(self, html):
		""" Tries to write a PDF export from the command line using PrinceXML
		    if available.
		"""
		html_with_toc = self.generate_toc(html.encode('utf_8', 'xmlcharrefreplace'))
		
		try:
			f = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
			f.write(html_with_toc)
			f.close()
		except Exception, e:
			raise IOError(u"Unable to create temporary file, aborting: %s" % e)
	
		tmp_pdf = self.write_pdf(f)
		try:
			call(['pdftk', tmp_pdf.name] + self.config['post_process'].split() + [self.destination_file])
		except Exception, e:
			raise EnvironmentError(u"Unable to post-process PDF file using "
                            	    "pdftk. Is it installed and available?\n%s" % e)

	def write_pdf(self, f):
		dummy_fh = open(os.path.devnull, 'w')

		try:
			tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
			tmp_pdf.close()
			
			command = ["prince", f.name, tmp_pdf.name]
			Popen(command, stderr=dummy_fh).communicate()
		except Exception, e:
			raise EnvironmentError(u"Unable to generate PDF file using "
                            	    "prince. Is it installed and available?\n%s" % e)
		finally:
			dummy_fh.close()
		return tmp_pdf
	
	def generate_toc(self, html):
		cmd = W3_PREFIX + 'toc'
		return Popen(cmd, stdout=PIPE, stdin=PIPE).communicate(input=html)[0]

	def read_config(self):
		import ConfigParser
		raw_config = ConfigParser.SafeConfigParser({
			'theme':       'default',
			'title':       'Avalanche Project',
			'destination': 'book.pdf',
			'post_process': 'cat 1-end output',
		})
		
		try:
			raw_config.read('avalanche.cfg')

			self.config = {}
			self.config['intro']  = raw_config.get('avalanche', 'intro').replace('\r', '').split('\n')
			self.config['source'] = raw_config.get('avalanche', 'source').replace('\r', '').split('\n')
			self.config['title']  = raw_config.get('avalanche', 'title')
			self.config['theme']  = raw_config.get('avalanche', 'theme')
			self.config['post_process']  = raw_config.get('avalanche', 'post_process')
			self.config['toc_enabled']   = raw_config.get('avalanche', 'toc_enabled')
			self.destination_file = raw_config.get('avalanche', 'destination')

		except Exception, e:
			print 'Failed to read the config: %s' % e
			return None	

		return self.config
	
	
	def main(self):
		config = self.read_config()
		if not config: return
	
		html = self.render()
		self.write(html)
	

if __name__ == '__main__':
	Avalanche().main()
