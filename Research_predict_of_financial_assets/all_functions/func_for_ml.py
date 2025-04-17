def split_data(data, train_ratio=0.85, val_ratio=0.1, test_ratio=0.05):
    
    '''функция по делению датасета на трейн, валидацию, тест'''

    n = len(data)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)

    train = data.iloc[:train_end]
    val = data.iloc[train_end:val_end]
    test = data.iloc[val_end:]

    return train, val, test
    
def return_x_y(data):

    x = data.drop(["Цена", "Откр.", "Макс.", "Мин."], axis = 1)
    y = data["Цена"]
    
    return x, y