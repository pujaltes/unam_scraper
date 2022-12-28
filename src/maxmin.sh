#!/bin/bash
sort -n | awk '
  BEGIN {
    OFS="\t"
    c = 0;
  }
  $1 ~ /^(\-)?[0-9]*(\.[0-9]*)?$/ {
    a[c++] = $1;
  }
  END {
    print a[0], a[c-1];
  }
'
