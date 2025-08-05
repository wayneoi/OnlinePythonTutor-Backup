#include <stdlib.h>

int main()
{
  char* arr = MC_NEW_ARRAY(char, 10);
  delete arr; // mismatch
  int x = 42;
}
