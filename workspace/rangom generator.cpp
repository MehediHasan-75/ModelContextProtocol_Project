#include <iostream>
#include <cstdlib>
#include <ctime>

int main() {
    // Seed the random number generator with the current time
    std::srand(std::time(0));

    // Generate a random number between 10 and 1000 (inclusive)
    int randomNumber = (std::rand() % 991) + 10;

    // Print the random number
    std::cout << "Random number between 10 and 1000: " << randomNumber << std::endl;

    return 0;
}