#!/bin/bash
# Execute this file to recompile locally
c++ -Wall -shared -fPIC -std=c++11 -foo -I/Users/michaelwathen/anaconda/lib/python2.7/site-packages/ffc/backends/ufc -I/Users/michaelwathen/.cache/dijitso/include ffc_element_ba0bebe4da549c7b7dbe7954579625625bcf8608.cpp -L/Users/michaelwathen/.cache/dijitso/lib -Wl,-rpath,/Users/michaelwathen/.cache/dijitso/lib -Wl,-install_name,/Users/michaelwathen/.cache/dijitso/lib/libdijitso-ffc_element_ba0bebe4da549c7b7dbe7954579625625bcf8608.so -olibdijitso-ffc_element_ba0bebe4da549c7b7dbe7954579625625bcf8608.so