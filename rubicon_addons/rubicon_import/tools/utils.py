
##
#%%
def _row_shift(row, i):
    """Shift the row from the index i. 
    It delete the row[i]
    """
    for i in range(i, len(row)-1):
        row[i] = row[i+1]
    del row[i+1]

def calibring_row(row, clues):
    """
    Calibrate a row given clues.
    
    clues : {
        row_index : filter (lambda -> bool)
    }
    """
    
    index_a = 0
    done = False 
    
    while not done:
        if clues.get(index_a):
            if not clues[index_a](row[index_a]):
                row[index_a-1] = str(row[index_a-1])+str(row[index_a])
                _row_shift(row, index_a)
                index_a -=1
        index_a +=1
        if index_a == len(row):
            break
# %%
