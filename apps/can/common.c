#include <stdio.h>
#include "common.h"

void print_set(int *set, char type)
{
  int i = 0;
  
  while (set[i]) {
    if (i) {
      printf(" ");
    }
    if (type == 'd') {
      printf("%d", set[i]);
    }
    else if (type == 'x') {
      printf("%x", set[i]);
    }
    i++;
  }

} 

void add_to_set(int *set, int element)
{
  int i = 0;
  
  while (set[i]) {

    /* Check if element is already in set */
    if (set[i] == element) {
      return;
    }
    i++;
  }

  /* Add element to set */
  set[i] = element;
}
