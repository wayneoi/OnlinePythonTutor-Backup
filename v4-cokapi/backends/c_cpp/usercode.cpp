#include <iostream>

int main() {
  int* x = new int[3];
  x[1] = 20;
  int* p = &x[1]; // pointer into middle
  const char** fruit = new const char*[3];
  fruit[1] = "bananas";
  std::cout << "Yum " << *p << " " << fruit[1];
  return 0;
}