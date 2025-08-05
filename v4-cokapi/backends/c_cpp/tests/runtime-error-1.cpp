#include <stdlib.h>

int main() {
  int* x = MC_NEW_ARRAY(int, 2);
  x[100] = 10;   // invalid write
  int y = x[10]; // invalid read
}
