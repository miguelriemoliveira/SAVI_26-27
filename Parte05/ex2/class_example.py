#!/usr/bin/env python3 
# Shebang line" specifies the interpreter. 

# imports --------------------
import argparse
from random import randint
import json
import signal
import sys
from matplotlib import pyplot as plt


# Main function
def main(): # this is our main function



    # -------------------------------------------------------------------------
    # All variables are loose
    # functions are also not connected to variables
    # -------------------------------------------------------------------------

    # nomes = ['Rodrigo', 'Samuel', 'Miguel', 'Guilherme']
    # idades = [22, 23, 21]

    # # How to do a birthday for someone? 

    # # First, find the index of the name we want

    # idx_rodrigo = 0

    # idades[idx_rodrigo] = idades[idx_rodrigo] + 1

    # def happy_birthday(nome, nomes, idades):

    #     idx = nomes.index(nome)

    #     idades[idx] += 1


    # happy_birthday('Miguel', nomes, idades)


    # happy_birthday('Guilherme', nomes, idades)
    # print('idades' + str(idades))

    # -------------------------------------------------------------------------
    # Object oriented -> Classes
    # -------------------------------------------------------------------------

    class Pessoa:

        # Class constructor: a function that is called at the beggining when the instance of the class is created
        def __init__(self, nome, idade):

            # Save to class properties the arguments of the contructor
            self.nome = nome
            self.idade = idade

        def happy_brithday(self):

            self.idade += 1 # increment age
            print('Happy birthday ' + self.nome + '!\n You are now ' + str(self.idade) + ' years old.')

        def __str__(self):
            return 'Eu sou o(a) ' + self.nome + ' e tenho ' + str(self.idade) + ' anos.'



    pessoas = []

    # Add a person to the list of persons
    pessoa = Pessoa('Rodrigo', 22)
    pessoas.append(pessoa) # add this person to the list

    pessoa = Pessoa('Samuel', 23)
    pessoas.append(pessoa) # add this person to the list

    pessoa = Pessoa('Miguel', 21)
    pessoas.append(pessoa) # add this person to the list



    # Print All persosn
    for pessoa in pessoas:

        print(pessoa)





if __name__ == "__main__":
    main()




