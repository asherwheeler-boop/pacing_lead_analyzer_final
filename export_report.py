
import pandas as pd
from io import BytesIO


def build_excel_report(front, right):

    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        front.to_excel(writer, sheet_name='Front', index=False)
        right.to_excel(writer, sheet_name='Right', index=False)

    return output.getvalue()
