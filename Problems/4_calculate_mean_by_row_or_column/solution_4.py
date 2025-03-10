def calculate_matrix_mean(
    matrix: list[list[float]],
    mode: str,
) -> list[float]:
    # Calculate mean by row or column
    if mode == 'column':
        return [sum(col) / len(matrix) for col in zip(*matrix)]
    elif mode == 'row':
        return [sum(row) / len(row) for row in matrix]
    else:
        raise ValueError("Mode must be 'row' or 'column'")



x = calculate_matrix_mean([[3,4,5,0]],"row")
for i in x :
    print(i)
