import sys
import tkinter.tix
from fractions import Fraction


def page_rank_calcualtor(vector, matrix):
    old_vector = vector
    new_vector = [Fraction() for x in range(len(vector))]
    while True:
        vector_index = 0
        for matrix_row in matrix:
            multiplication_sum = Fraction()
            index = 0
            for number in matrix_row:
                multiplication_sum = multiplication_sum.__add__(
                    old_vector[index].__mul__(number))
                index += 1
            multiplication_sum = multiplication_sum.__mul__(Fraction(8, 10))
            multiplication_sum = multiplication_sum.__add__(Fraction(2, 10).__truediv__(Fraction(len(vector), 1)))

            new_vector[vector_index] = multiplication_sum
            vector_index += 1
        # Comparing old and new vectors
        min_difference = sys.maxsize
        for index in range(len(new_vector)):
            diff = abs(old_vector[index] - new_vector[index])
            if diff < min_difference:
                min_difference = diff
        old_vector = [new_vector[x] for x in range(len(new_vector))]

        if min_difference < 0.00001:
            break

    return new_vector


if __name__ == "__main__":
    matrix = [[0 for x in range(5)] for y in range(5)]
    vector = [Fraction(1, 5) for x in range(5)]

    matrix[0] = [Fraction(1, 3), Fraction(1, 3), Fraction(1, 2), Fraction(1, 4), 0]
    matrix[1] = [Fraction(1, 3), Fraction(1, 3), 0, Fraction(1, 4), 0]
    matrix[2] = [Fraction(1, 3), Fraction(1, 3), 0, Fraction(1, 4), Fraction(1, 1)]
    matrix[3] = [0, 0, 0, 0, 0]
    matrix[4] = [0, 0, Fraction(1, 2), Fraction(1, 4), 0]

    for row in matrix:
        print(row)

    print(f"My vector : {vector}")

    print(page_rank_calcualtor(vector=vector, matrix=matrix))
