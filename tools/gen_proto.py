#!/usr/bin/python
"""
Python Sock tools: gen_proto.py - Generate a python module for parsing a custom protocol
Copyright (C) 2016 GarethNelson

This file is part of python-sock-tools

python-sock-tools is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

python-sock-tools is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with python-sock-tools.  If not, see <http://www.gnu.org/licenses/>.
"""

import eventlet
import argparse
import json
import time

def get_parser():
    parser = argparse.ArgumentParser(description='Autogenerate a python module that implements a custom protocol')
    parser.add_argument('-s','--specfile',type=str,help='The specification file to use',required=True)
    parser.add_argument('-t','--template',type=str,help='The location of the templates directory to use')
    parser.add_argument('-o','--output',  type=str,help='Where to write output',default='generated.py')
    return parser

def load_json_file(path):
    json_fd = open(path,'r')
    retval = json.load(json_fd)
    json_fd.close()
    return retval

def load_template(path,template_name):
    template_filename = os.path.join(path,template_name)
    fd = open(template_filename,'r')
    retval = fd.read()
    fd.close()
    return retval

def get_template_vars(specdata,filename):
    retval = {'%%PROTONAME%%':specdata['protocol_name'],
              '%%PROTOSOCK%%':specdata['protocol_sock'],
              '%%SPECFILE%%': filename,
              '%%DATETIME%%':time.ctime().upper(),
              '%%MIXINS%%':  ','.join(specdata['mixins']),
              '%%IMPORTS%%':'',
              '%%HANDLERS%%':''}
    for modname in specdata['imports']:
        retval['%%IMPORTS%%'] += ('import %s\n' % modname)
    msg_handlers_dict = {}
    for msg in specdata['messages']:
        msg_handlers_dict[msg['msg_type_int']] = '[self._handle_%s]' % msg['msg_type_str']
        param_str = ''
        if specdata['named_fields']:
           param_str = ','.join(map(lambda x: x+'=None',msg['fields']))
           retval['%%HANDLERS%%'] += '\n   def _handle_%s(self,from_addr,msg_type,msg_data):\n       self.handle_%s(from_addr,**msg_data)' % (msg['msg_type_str'],msg['msg_type_str'])
        else:
           param_str = ','.join(msg['fields'])
           retval['%%HANDLERS%%'] += '\n   def _handle_%s(self,from_addr,msg_type,msg_data):\n       self.handle_%s(from_addr,*msg_data)' % (msg['msg_type_str'],msg['msg_type_str'])
        retval['%%HANDLERS%%'] += '\n   def handle_%s(self,from_addr,%s):\n       pass' % (msg['msg_type_str'],param_str)
    msghandlers_str = repr(msg_handlers_dict)
    msghandlers_str = msghandlers_str.replace('u\'','')
    msghandlers_str = msghandlers_str.replace('\'','')
    retval['%%HANDLERS_DICT%%'] = msghandlers_str
    return retval

def load_templates(path):
    retval = {'module':load_template(path,"module"),
              'protoclass':load_template(path,'protoclass')}
    return retval

if __name__=='__main__':
   import os
   
   args = get_parser().parse_args()
   if args.template is None:
      template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates')
   else:
      template_path = args.template
   print 'Loading specification from %s' % os.path.abspath(args.specfile)
   specdata  = load_json_file(os.path.abspath(args.specfile))
   print 'Loading templates from %s' % template_path
   templates = load_templates(template_path)
   
   template_vars = get_template_vars(specdata,os.path.abspath(args.specfile))

   print 'Rendering templates'
   for x in xrange(2):
       for k,v in templates.items():
           for var_k,var_v in template_vars.items():
               if var_k in v:
                  templates[k] = templates[k].replace(var_k,var_v)
           for t_k,t_v in templates.items():
               if ('%%%%%s%%%%' % t_k.upper()) in v:
                  templates[k] = templates[k].replace('%%%%%s%%%%' % t_k.upper(),templates[t_k])

   output_file = open(args.output,'w')
   output_file.write(templates['module'])



