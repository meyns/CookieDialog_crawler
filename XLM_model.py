import XLM_model_execute

print('1: Cookie dialog model')
print('2: Buttons model model')
choice = int(input('Which model would you like to train? '))
choice_runs = int(input('How many runs do you want to do? '))
print('')

# Variabelen voorbereiden
if choice == 1:
    number_of_runs = choice_runs
    classification_filename = 'D:/Documenten/Maarten/Open universiteit/VAF/DATA/Classification file for cookie dialog.csv'
    model_savedir = "D:/temp/training model cookie dialog/"
    model_type = "cookie dialog"
elif choice == 2:
    number_of_runs = choice_runs
    classification_filename = 'D:/Documenten/Maarten/Open universiteit/VAF/DATA/Classification file for buttons.csv'
    model_savedir = "D:/temp/training model buttons/"
    model_type = "buttons"

XLM_model_execute.main(number_of_runs, classification_filename, model_savedir, model_type)
